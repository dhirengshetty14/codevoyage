"""
Git repository analysis service
Handles cloning and analyzing Git repositories
"""

import os
import shutil
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import git
from git import Repo
from git.remote import RemoteProgress
import structlog

from app.core.config import settings
from app.core.circuit_breaker import circuit_breaker

logger = structlog.get_logger()


class GitService:
    """Service for Git operations"""
    
    class _CloneProgress(RemoteProgress):
        def __init__(self, callback: Optional[Callable[[int, str], None]] = None):
            super().__init__()
            self.callback = callback
            self.last_percent = -1

        def update(self, op_code, cur_count, max_count=None, message=""):
            if not self.callback or not max_count:
                return
            try:
                percent = int((cur_count / max_count) * 100)
            except Exception:
                return
            if percent >= self.last_percent + 2:
                self.last_percent = percent
                self.callback(min(100, max(0, percent)), message or "cloning")

    def __init__(self):
        self.temp_path = settings.TEMP_STORAGE_PATH
        os.makedirs(self.temp_path, exist_ok=True)
    
    @circuit_breaker(failure_threshold=3, timeout=300)
    def clone_repository(
        self,
        url: str,
        repo_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> str:
        """Clone a Git repository"""
        clone_path = os.path.join(self.temp_path, repo_id)
        
        # Remove existing directory if it exists
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)
        
        try:
            logger.info("Cloning repository", url=url, path=clone_path)
            Repo.clone_from(
                url,
                clone_path,
                depth=settings.GIT_CLONE_DEPTH,
                single_branch=True,
                no_tags=True,
                progress=self._CloneProgress(progress_callback),
            )
            logger.info("Repository cloned successfully", path=clone_path)
            return clone_path
        except Exception as e:
            logger.error("Failed to clone repository", error=str(e), url=url)
            raise
    
    def get_commits(
        self,
        repo_path: str,
        max_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all commits from repository"""
        try:
            repo = Repo(repo_path)
            commits = []
            
            max_commits = max_count or settings.MAX_COMMITS_TO_ANALYZE
            
            for idx, commit in enumerate(repo.iter_commits(max_count=max_commits)):
                # Computing diff stats for every commit is expensive on large repos.
                # Limit detailed stats to recent commits for responsiveness.
                if idx < settings.COMMIT_STATS_LIMIT:
                    stats = commit.stats.total
                else:
                    stats = {'files': 0, 'insertions': 0, 'deletions': 0}

                commits.append({
                    'sha': commit.hexsha,
                    'message': commit.message,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'committed_at': datetime.fromtimestamp(commit.committed_date),
                    'stats': stats
                })
            
            logger.info("Commits extracted", count=len(commits), repo_path=repo_path)
            return commits
        except Exception as e:
            logger.error("Failed to get commits", error=str(e), repo_path=repo_path)
            raise
    
    def get_file_tree(self, repo_path: str, commit_sha: Optional[str] = None) -> Dict[str, Any]:
        """Get file tree structure"""
        try:
            repo = Repo(repo_path)
            
            if commit_sha:
                commit = repo.commit(commit_sha)
            else:
                commit = repo.head.commit
            
            tree_data = self._build_tree(commit.tree, "")
            
            logger.info("File tree extracted", repo_path=repo_path)
            return tree_data
        except Exception as e:
            logger.error("Failed to get file tree", error=str(e), repo_path=repo_path)
            raise
    
    def _build_tree(self, tree, path: str) -> Dict[str, Any]:
        """Recursively build file tree"""
        result = {
            'name': os.path.basename(path) or 'root',
            'path': path,
            'type': 'directory',
            'children': []
        }
        
        for item in tree:
            item_path = os.path.join(path, item.name)
            
            if item.type == 'tree':
                # Directory
                result['children'].append(self._build_tree(item, item_path))
            else:
                # File
                result['children'].append({
                    'name': item.name,
                    'path': item_path,
                    'type': 'file',
                    'size': item.size
                })
        
        return result
    
    def get_contributors(self, repo_path: str, max_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all contributors"""
        try:
            repo = Repo(repo_path)
            contributors = {}
            
            max_commits = max_count or settings.MAX_COMMITS_TO_ANALYZE
            for commit in repo.iter_commits(max_count=max_commits):
                email = commit.author.email
                
                if email not in contributors:
                    contributors[email] = {
                        'name': commit.author.name,
                        'email': email,
                        'commits': 0,
                        'first_commit': commit.committed_datetime,
                        'last_commit': commit.committed_datetime
                    }
                
                contributors[email]['commits'] += 1
                
                if commit.committed_datetime < contributors[email]['first_commit']:
                    contributors[email]['first_commit'] = commit.committed_datetime
                if commit.committed_datetime > contributors[email]['last_commit']:
                    contributors[email]['last_commit'] = commit.committed_datetime
            
            logger.info("Contributors extracted", count=len(contributors))
            return list(contributors.values())
        except Exception as e:
            logger.error("Failed to get contributors", error=str(e))
            raise
    
    def get_file_history(self, repo_path: str, file_path: str) -> List[Dict[str, Any]]:
        """Get commit history for a specific file"""
        try:
            repo = Repo(repo_path)
            commits = []
            
            for commit in repo.iter_commits(paths=file_path):
                commits.append({
                    'sha': commit.hexsha,
                    'author': commit.author.name,
                    'date': datetime.fromtimestamp(commit.committed_date),
                    'message': commit.message
                })
            
            return commits
        except Exception as e:
            logger.error("Failed to get file history", error=str(e), file_path=file_path)
            raise
    
    def cleanup(self, repo_path: str):
        """Clean up cloned repository"""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info("Repository cleaned up", path=repo_path)
        except Exception as e:
            logger.error("Failed to cleanup repository", error=str(e), path=repo_path)
