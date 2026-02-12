"""
Code complexity analysis service
Uses radon and lizard for complexity metrics
"""

import os
from typing import Dict, Any, List
import radon.complexity as radon_cc
from radon.raw import analyze
import lizard
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ComplexityService:
    """Service for code complexity analysis"""
    
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
        '.cs', '.go', '.rb', '.php', '.swift', '.kt'
    }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze complexity of a single file"""
        try:
            _, ext = os.path.splitext(file_path)
            
            if ext not in self.SUPPORTED_EXTENSIONS:
                return {'supported': False}
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Use radon for Python files
            if ext == '.py':
                return self._analyze_python(content, file_path)
            
            # Use lizard for other languages
            return self._analyze_with_lizard(file_path)
        except Exception as e:
            logger.error("Failed to analyze file complexity", error=str(e), file=file_path)
            return {'error': str(e)}
    
    def _analyze_python(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Python file with radon"""
        try:
            # Cyclomatic complexity
            cc_results = radon_cc.cc_visit(content)
            avg_complexity = sum(r.complexity for r in cc_results) / len(cc_results) if cc_results else 0
            
            # Raw metrics
            raw_metrics = analyze(content)
            
            return {
                'supported': True,
                'cyclomatic_complexity': avg_complexity,
                'lines_of_code': raw_metrics.loc,
                'logical_lines': raw_metrics.lloc,
                'comments': raw_metrics.comments,
                'blank_lines': raw_metrics.blank,
                'maintainability_index': self._calculate_maintainability(raw_metrics, avg_complexity)
            }
        except Exception as e:
            logger.error("Failed to analyze Python file", error=str(e))
            return {'error': str(e)}
    
    def _analyze_with_lizard(self, file_path: str) -> Dict[str, Any]:
        """Analyze file with lizard"""
        try:
            analysis = lizard.analyze_file(file_path)
            
            if not analysis.function_list:
                return {
                    'supported': True,
                    'cyclomatic_complexity': 0,
                    'lines_of_code': analysis.nloc
                }
            
            avg_complexity = sum(f.cyclomatic_complexity for f in analysis.function_list) / len(analysis.function_list)
            
            return {
                'supported': True,
                'cyclomatic_complexity': avg_complexity,
                'lines_of_code': analysis.nloc,
                'token_count': analysis.token_count,
                'function_count': len(analysis.function_list)
            }
        except Exception as e:
            logger.error("Failed to analyze with lizard", error=str(e))
            return {'error': str(e)}
    
    def _calculate_maintainability(self, raw_metrics, complexity: float) -> float:
        """Calculate maintainability index"""
        # Simplified maintainability index calculation
        # MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(L)
        # Where V = volume, G = complexity, L = lines of code
        
        import math
        
        try:
            volume = raw_metrics.lloc * math.log(raw_metrics.lloc + 1)
            mi = 171 - 5.2 * math.log(volume + 1) - 0.23 * complexity - 16.2 * math.log(raw_metrics.loc + 1)
            return max(0, min(100, mi))  # Normalize to 0-100
        except:
            return 50.0  # Default middle value
    
    def analyze_directory(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze all files in a directory"""
        results = []
        scanned = 0
        max_files = settings.MAX_FILES_FOR_COMPLEXITY
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', 'venv', 'env'}]
            
            for file in files:
                if scanned >= max_files:
                    logger.info("Complexity scan capped", max_files=max_files)
                    logger.info("Directory analyzed", file_count=len(results))
                    return results

                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext in self.SUPPORTED_EXTENSIONS:
                    scanned += 1
                    relative_path = os.path.relpath(file_path, repo_path)
                    analysis = self.analyze_file(file_path)
                    
                    if analysis.get('supported'):
                        results.append({
                            'path': relative_path,
                            'filename': file,
                            'extension': ext,
                            **analysis
                        })
        
        logger.info("Directory analyzed", file_count=len(results))
        return results
