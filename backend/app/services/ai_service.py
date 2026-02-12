"""
AI-powered insights service using OpenAI GPT-4
"""

from typing import Dict, Any, List
import json
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.core.circuit_breaker import circuit_breaker

logger = structlog.get_logger()


class AIService:
    """Service for AI-powered code analysis"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    @circuit_breaker(failure_threshold=3, timeout=120)
    async def analyze_coding_patterns(
        self,
        commits: List[Dict[str, Any]],
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze coding patterns from commits and files"""
        if not settings.ENABLE_AI_INSIGHTS:
            return {"enabled": False}
        
        try:
            # Prepare data summary for GPT-4
            summary = self._prepare_pattern_summary(commits, files)
            
            prompt = f"""Analyze this codebase and identify key coding patterns:

{summary}

Provide insights on:
1. Common coding patterns and practices
2. Code organization approach
3. Technology stack evolution
4. Development workflow patterns
5. Notable refactoring events

Return response as JSON with keys: patterns, practices, evolution, workflow, refactorings"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert code analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Coding patterns analyzed")
            return result
        except Exception as e:
            logger.error("Failed to analyze coding patterns", error=str(e))
            return {"error": str(e)}
    
    @circuit_breaker(failure_threshold=3, timeout=120)
    async def analyze_team_dynamics(
        self,
        contributors: List[Dict[str, Any]],
        commits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze team collaboration and dynamics"""
        if not settings.ENABLE_AI_INSIGHTS:
            return {"enabled": False}
        
        try:
            summary = self._prepare_team_summary(contributors, commits)
            
            prompt = f"""Analyze team collaboration patterns:

{summary}

Provide insights on:
1. Team structure and roles
2. Collaboration patterns
3. Work distribution
4. Development habits (e.g., midnight coders)
5. Knowledge silos or bottlenecks

Return response as JSON with keys: structure, collaboration, distribution, habits, bottlenecks"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in software team dynamics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Team dynamics analyzed")
            return result
        except Exception as e:
            logger.error("Failed to analyze team dynamics", error=str(e))
            return {"error": str(e)}
    
    @circuit_breaker(failure_threshold=3, timeout=120)
    async def detect_migrations(
        self,
        language_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect technology migrations"""
        if not settings.ENABLE_AI_INSIGHTS:
            return {"enabled": False}
        
        try:
            prompt = f"""Analyze language/technology evolution:

{json.dumps(language_stats, indent=2)}

Identify:
1. Major technology migrations (e.g., jQuery → React, Python 2 → 3)
2. New technologies adopted
3. Deprecated technologies
4. Migration timeline and impact

Return response as JSON with keys: migrations, adoptions, deprecations, timeline"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in technology stack evolution."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Technology migrations detected")
            return result
        except Exception as e:
            logger.error("Failed to detect migrations", error=str(e))
            return {"error": str(e)}
    
    def _prepare_pattern_summary(
        self,
        commits: List[Dict[str, Any]],
        files: List[Dict[str, Any]]
    ) -> str:
        """Prepare summary for pattern analysis"""
        total_commits = len(commits)
        file_extensions = {}
        
        for file in files:
            ext = file.get('extension', 'unknown')
            file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        return f"""
Total Commits: {total_commits}
File Types: {json.dumps(file_extensions, indent=2)}
Recent Commits: {json.dumps(commits[:10], indent=2, default=str)}
"""
    
    def _prepare_team_summary(
        self,
        contributors: List[Dict[str, Any]],
        commits: List[Dict[str, Any]]
    ) -> str:
        """Prepare summary for team analysis"""
        return f"""
Total Contributors: {len(contributors)}
Total Commits: {len(commits)}
Top Contributors: {json.dumps(contributors[:10], indent=2, default=str)}
Commit Timeline: {json.dumps(commits[:20], indent=2, default=str)}
"""
