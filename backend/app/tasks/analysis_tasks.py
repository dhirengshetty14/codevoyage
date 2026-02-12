"""
Celery tasks for distributed repository analysis
"""

import asyncio
from datetime import datetime
from celery import current_task
import structlog

from app.tasks.celery_app import celery_app
from app.services.git_service import GitService
from app.services.ai_service import AIService
from app.services.complexity_service import ComplexityService
from app.services.insight_service import InsightService
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.analysis import Analysis
from app.models.commit import Commit
from app.models.file import File
from app.models.contributor import Contributor
from app.core.cache import cache_manager
from app.core.realtime import publish_progress_event

logger = structlog.get_logger()
_TASK_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_TASK_LOOP)


def _run_async(coro):
    """Run all async task coroutines on a single dedicated loop."""
    return _TASK_LOOP.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def start_repository_analysis(self, analysis_id: str, repository_id: str):
    """Main analysis task - orchestrates the distributed analysis pipeline"""
    try:
        # Update analysis status
        update_progress(analysis_id, 0, "starting")
        
        # Start sub-tasks
        chain = (
            analyze_git_data.s(analysis_id, repository_id) |
            analyze_complexity.s(analysis_id, repository_id) |
            generate_ai_insights.s(analysis_id, repository_id) |
            compile_results.s(analysis_id, repository_id)
        )
        
        result = chain.apply_async()
        
        logger.info("Analysis pipeline started", analysis_id=analysis_id, task_id=result.id)
        return result.id
    except Exception as e:
        logger.error("Failed to start analysis pipeline", error=str(e), analysis_id=analysis_id)
        update_progress(analysis_id, 0, "failed", str(e))
        raise


@celery_app.task(bind=True, max_retries=3)
def analyze_git_data(self, analysis_id: str, repository_id: str):
    """Analyze Git repository data"""
    try:
        update_progress(analysis_id, 10, "analyzing_git_data")

        async def get_repository():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(Repository).where(Repository.id == repository_id)
                )
                return result.scalar_one()

        repository = _run_async(get_repository())
        git_service = GitService()
        cache_key = f"git_analysis:{repository_id}"

        cached_data = _run_async(cache_manager.get(cache_key))
        if cached_data:
            logger.info("Using cached git analysis", repo_id=repository_id)
            update_progress(analysis_id, 40, "git_analysis_complete")
            return cached_data

        def clone_progress(percent: int, _message: str):
            # Map clone 0..100 to stage progress 12..20
            mapped = 12 + int((percent / 100) * 8)
            update_progress(analysis_id, mapped, "cloning_repository")

        clone_path = git_service.clone_repository(
            repository.url,
            str(repository.id),
            progress_callback=clone_progress,
        )
        update_progress(analysis_id, 20, "git_clone_complete")

        commits = git_service.get_commits(clone_path)
        update_progress(analysis_id, 28, "commit_extraction_complete")

        contributors = git_service.get_contributors(
            clone_path,
            max_count=settings.MAX_COMMITS_TO_ANALYZE,
        )
        update_progress(analysis_id, 34, "contributor_extraction_complete")

        file_tree = git_service.get_file_tree(clone_path)
        update_progress(analysis_id, 38, "file_tree_extraction_complete")

        language_stats = extract_language_stats(file_tree)
        git_service.cleanup(clone_path)

        result_data = {
            "commits": commits,
            "contributors": contributors,
            "file_tree": file_tree,
            "language_stats": language_stats,
            "total_commits": len(commits),
            "total_contributors": len(contributors)
        }

        _run_async(cache_manager.set(cache_key, make_json_safe(result_data), 3600))
        
        update_progress(analysis_id, 40, "git_analysis_complete")
        logger.info("Git analysis completed", analysis_id=analysis_id)
        
        return result_data
    except Exception as e:
        logger.error("Git analysis failed", error=str(e), analysis_id=analysis_id)
        update_progress(analysis_id, 10, "failed", str(e))
        raise


@celery_app.task(bind=True, max_retries=3)
def analyze_complexity(self, git_data: dict, analysis_id: str, repository_id: str):
    """Analyze code complexity"""
    try:
        update_progress(analysis_id, 50, "analyzing_complexity")
        
        async def process():
            async with AsyncSessionLocal() as db:
                # Get repository
                from sqlalchemy import select
                result = await db.execute(
                    select(Repository).where(Repository.id == repository_id)
                )
                repository = result.scalar_one()
                
                # Initialize services
                git_service = GitService()
                complexity_service = ComplexityService()
                
                # Clone repository
                clone_path = git_service.clone_repository(repository.url, str(repository.id) + "_complexity")
                
                # Analyze complexity
                complexity_results = complexity_service.analyze_directory(clone_path)
                
                # Extract hotspots (most complex files)
                hotspots = sorted(
                    complexity_results,
                    key=lambda x: x.get('cyclomatic_complexity', 0),
                    reverse=True
                )[:20]
                
                # Cleanup
                git_service.cleanup(clone_path)
                
                result_data = {
                    "complexity_metrics": complexity_results,
                    "hotspots": hotspots
                }
                
                return result_data
        
        result_data = _run_async(process())
        update_progress(analysis_id, 60, "complexity_scan_complete")
        
        update_progress(analysis_id, 70, "complexity_analysis_complete")
        logger.info("Complexity analysis completed", analysis_id=analysis_id)
        
        return {**git_data, **result_data}
    except Exception as e:
        logger.error("Complexity analysis failed", error=str(e), analysis_id=analysis_id)
        update_progress(analysis_id, 50, "failed", str(e))
        raise


@celery_app.task(bind=True, max_retries=3)
def generate_ai_insights(self, combined_data: dict, analysis_id: str, repository_id: str):
    """Generate AI-powered insights"""
    try:
        update_progress(analysis_id, 80, "generating_ai_insights")
        insight_service = InsightService()
        deterministic_insights = insight_service.build_insights(
            combined_data.get("commits", []),
            combined_data.get("contributors", []),
            combined_data.get("complexity_metrics", []),
            combined_data.get("hotspots", []),
            combined_data.get("language_stats", {}),
            combined_data.get("file_tree"),
        )

        if not settings.ENABLE_AI_INSIGHTS or not settings.OPENAI_API_KEY:
            logger.info("Skipping AI insights (disabled or missing key)", analysis_id=analysis_id)
            update_progress(analysis_id, 90, "ai_insights_skipped")
            return {
                **combined_data,
                "ai_insights": {
                    "enabled": False,
                    "reason": "missing_or_disabled_api_key",
                    "deterministic_insights": deterministic_insights,
                },
            }
        
        async def process():
            ai_service = AIService()
            
            # Generate insights
            coding_patterns = await ai_service.analyze_coding_patterns(
                combined_data.get('commits', []),
                combined_data.get('complexity_metrics', [])
            )
            
            team_dynamics = await ai_service.analyze_team_dynamics(
                combined_data.get('contributors', []),
                combined_data.get('commits', [])
            )
            
            migrations = await ai_service.detect_migrations(
                combined_data.get('language_stats', {})
            )
            
            result_data = {
                "ai_insights": {
                    "enabled": True,
                    "deterministic_insights": deterministic_insights,
                    "coding_patterns": coding_patterns,
                    "team_dynamics": team_dynamics,
                    "migrations": migrations
                }
            }
            
            return result_data
        
        try:
            result_data = _run_async(process())
        except Exception as ai_error:
            logger.warning("LLM insights failed, continuing with deterministic insights", error=str(ai_error))
            result_data = {
                "ai_insights": {
                    "enabled": False,
                    "reason": "llm_generation_failed",
                    "error": str(ai_error),
                    "deterministic_insights": deterministic_insights,
                }
            }
        
        update_progress(analysis_id, 90, "ai_insights_generated")
        logger.info("AI insights generated", analysis_id=analysis_id)
        
        return {**combined_data, **result_data}
    except Exception as e:
        logger.error("AI insights generation failed", error=str(e), analysis_id=analysis_id)
        update_progress(analysis_id, 80, "failed", str(e))
        raise


@celery_app.task(bind=True, max_retries=3)
def compile_results(self, final_data: dict, analysis_id: str, repository_id: str):
    """Compile all results and update database"""
    try:
        update_progress(analysis_id, 95, "compiling_results")
        safe_data = make_json_safe(final_data)
        
        async def process():
            async with AsyncSessionLocal() as db:
                # Get analysis
                from sqlalchemy import select
                result = await db.execute(
                    select(Analysis).where(Analysis.id == analysis_id)
                )
                analysis = result.scalar_one()
                
                # Update analysis with results
                analysis.status = "completed"
                analysis.progress = 100
                analysis.completed_at = datetime.utcnow()
                analysis.file_tree_data = safe_data.get('file_tree')
                analysis.contributor_network = safe_data.get('contributors')
                analysis.complexity_metrics = safe_data.get('complexity_metrics')
                analysis.hotspots = safe_data.get('hotspots')
                analysis.language_evolution = safe_data.get('language_stats')
                analysis.ai_insights = safe_data.get('ai_insights')
                analysis.commits_analyzed = len(safe_data.get('commits', []))
                if analysis.created_at:
                    analysis.processing_time_seconds = int(
                        (datetime.utcnow() - analysis.created_at.replace(tzinfo=None)).total_seconds()
                    )
                else:
                    analysis.processing_time_seconds = 0
                
                # Update repository stats
                result = await db.execute(
                    select(Repository).where(Repository.id == repository_id)
                )
                repository = result.scalar_one()
                
                repository.total_commits = len(safe_data.get('commits', []))
                repository.total_contributors = len(safe_data.get('contributors', []))
                repository.total_files = len(safe_data.get('complexity_metrics', []))
                repository.is_analyzed = True
                repository.last_analyzed_at = datetime.utcnow()
                
                await db.commit()
                
                return {
                    "analysis_id": analysis_id,
                    "repository_id": repository_id,
                    "total_commits": repository.total_commits,
                    "total_contributors": repository.total_contributors,
                    "total_files": repository.total_files
                }
        
        result_data = _run_async(process())
        
        update_progress(analysis_id, 100, "completed")
        logger.info("Analysis completed", analysis_id=analysis_id)
        
        return result_data
    except Exception as e:
        logger.error("Failed to compile results", error=str(e), analysis_id=analysis_id)
        update_progress(analysis_id, 95, "failed", str(e))
        raise


def update_progress(analysis_id: str, progress: int, status: str, error_message: str = None):
    """Update analysis progress and broadcast via WebSocket"""
    try:
        async def update():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, update
                
                # Update database
                stmt = update(Analysis).where(Analysis.id == analysis_id).values(
                    progress=progress,
                    status=status,
                    error_message=error_message
                )
                await db.execute(stmt)
                await db.commit()
                
                # Broadcast via Redis Pub/Sub for API websocket fanout
                await publish_progress_event({
                    'analysis_id': analysis_id,
                    'progress': progress,
                    'status': status,
                    'error_message': error_message
                })
        
        _run_async(update())
        
    except Exception as e:
        logger.error("Failed to update progress", error=str(e), analysis_id=analysis_id)


def extract_language_stats(file_tree: dict) -> dict:
    """Extract language statistics from file tree"""
    lang_stats = {}
    
    def traverse(node):
        if node.get('type') == 'file':
            _, ext = node.get('path', '').rsplit('.', 1) if '.' in node.get('path', '') else ('', '')
            if ext:
                lang_stats[ext] = lang_stats.get(ext, 0) + 1
        
        for child in node.get('children', []):
            traverse(child)
    
    traverse(file_tree)
    return lang_stats


def make_json_safe(value):
    """Recursively convert datetime-like values to JSON-safe values."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    return value
