"""
Analysis API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import structlog

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models.analysis import Analysis
from app.models.repository import Repository
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.tasks.analysis_tasks import start_repository_analysis

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=AnalysisResponse)
@limiter.limit("5/minute")
async def create_analysis(
    request: Request,
    analysis_data: AnalysisCreate,
    db: AsyncSession = Depends(get_db)
):
    """Start a new repository analysis"""
    # Check if repository exists
    result = await db.execute(
        select(Repository).where(Repository.id == analysis_data.repository_id)
    )
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Create analysis record
    analysis = Analysis(
        repository_id=analysis_data.repository_id,
        status="pending"
    )
    
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    # Start async analysis task
    start_repository_analysis.delay(str(analysis.id), str(repository.id))
    
    logger.info(
        "Analysis started",
        analysis_id=str(analysis.id),
        repo_id=str(repository.id)
    )
    
    return analysis


@router.get("/stats")
async def get_analysis_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get aggregate analysis stats for dashboard cards."""
    total_result = await db.execute(select(func.count(Analysis.id)))
    completed_result = await db.execute(
        select(func.count(Analysis.id)).where(Analysis.status == "completed")
    )
    failed_result = await db.execute(
        select(func.count(Analysis.id)).where(Analysis.status == "failed")
    )
    running_result = await db.execute(
        select(func.count(Analysis.id)).where(
            Analysis.status.in_(["pending", "starting", "analyzing_git_data", "analyzing_complexity", "generating_ai_insights", "compiling_results"])
        )
    )

    return {
        "total_analyses": total_result.scalar_one() or 0,
        "completed": completed_result.scalar_one() or 0,
        "failed": failed_result.scalar_one() or 0,
        "running": running_result.scalar_one() or 0,
    }


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get analysis by ID"""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis


@router.get("/repository/{repository_id}", response_model=List[AnalysisResponse])
async def list_repository_analyses(
    repository_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all analyses for a repository"""
    result = await db.execute(
        select(Analysis)
        .where(Analysis.repository_id == repository_id)
        .order_by(Analysis.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    analyses = result.scalars().all()
    return analyses


@router.get("/repository/{repository_id}/snapshot-diff")
async def latest_snapshot_diff(
    repository_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Compare the two most recent completed analyses for a repository."""
    result = await db.execute(
        select(Analysis)
        .where(Analysis.repository_id == repository_id, Analysis.status == "completed")
        .order_by(Analysis.created_at.desc())
        .limit(2)
    )
    analyses = result.scalars().all()
    if len(analyses) < 2:
        raise HTTPException(status_code=404, detail="Need at least two completed analyses for diff")
    return _build_snapshot_diff(analyses[1], analyses[0])


@router.get("/{analysis_id}/snapshot-diff")
async def analysis_snapshot_diff(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Compare a completed analysis with the immediately previous completed analysis."""
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    current = result.scalar_one_or_none()
    if not current:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if current.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis must be completed")

    prev_result = await db.execute(
        select(Analysis)
        .where(
            Analysis.repository_id == current.repository_id,
            Analysis.status == "completed",
            Analysis.created_at < current.created_at,
        )
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    previous = prev_result.scalar_one_or_none()
    if not previous:
        raise HTTPException(status_code=404, detail="No previous completed analysis found")

    return _build_snapshot_diff(previous, current)


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete analysis"""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    await db.delete(analysis)
    await db.commit()
    
    logger.info("Analysis deleted", analysis_id=analysis_id)
    
    return {"message": "Analysis deleted successfully"}


def _build_snapshot_diff(base: Analysis, target: Analysis):
    base_insights = (base.ai_insights or {}).get("deterministic_insights", {})
    target_insights = (target.ai_insights or {}).get("deterministic_insights", {})

    def pick_score(insights, key):
        return ((insights.get("health_scorecard") or {}).get("dimensions") or {}).get(key, 0)

    base_health = (base_insights.get("health_scorecard") or {}).get("overall_score", 0)
    target_health = (target_insights.get("health_scorecard") or {}).get("overall_score", 0)
    base_hot = (base_insights.get("complexity_profile") or {}).get("high_risk_file_count", 0)
    target_hot = (target_insights.get("complexity_profile") or {}).get("high_risk_file_count", 0)

    return {
        "base_analysis_id": str(base.id),
        "target_analysis_id": str(target.id),
        "summary_diff": {
            "commits_analyzed_delta": (target.commits_analyzed or 0) - (base.commits_analyzed or 0),
            "processing_time_delta_seconds": (target.processing_time_seconds or 0) - (base.processing_time_seconds or 0),
            "health_score_delta": round(target_health - base_health, 2),
            "high_risk_files_delta": (target_hot or 0) - (base_hot or 0),
        },
        "scorecard_diff": {
            "ownership_resilience_delta": round(
                pick_score(target_insights, "ownership_resilience") - pick_score(base_insights, "ownership_resilience"), 2
            ),
            "delivery_reliability_delta": round(
                pick_score(target_insights, "delivery_reliability") - pick_score(base_insights, "delivery_reliability"), 2
            ),
            "complexity_health_delta": round(
                pick_score(target_insights, "complexity_health") - pick_score(base_insights, "complexity_health"), 2
            ),
            "analysis_coverage_delta": round(
                pick_score(target_insights, "analysis_coverage") - pick_score(base_insights, "analysis_coverage"), 2
            ),
            "engineering_velocity_delta": round(
                pick_score(target_insights, "engineering_velocity") - pick_score(base_insights, "engineering_velocity"), 2
            ),
            "architecture_balance_delta": round(
                pick_score(target_insights, "architecture_balance") - pick_score(base_insights, "architecture_balance"), 2
            ),
        },
        "fingerprint": {
            "base": (base_insights.get("repo_fingerprint") or {}).get("tagline"),
            "target": (target_insights.get("repo_fingerprint") or {}).get("tagline"),
        },
    }
