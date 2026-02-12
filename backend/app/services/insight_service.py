"""
Deterministic repository insights.
Produces rich analytics without depending on LLM availability.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
import math
from statistics import median
from typing import Any, Dict, List


REFACTOR_KEYWORDS = (
    "refactor",
    "rewrite",
    "cleanup",
    "migrate",
    "rename",
    "extract",
    "modular",
)


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class InsightService:
    """Builds analysis insights from git/complexity outputs."""

    def build_insights(
        self,
        commits: List[Dict[str, Any]],
        contributors: List[Dict[str, Any]],
        complexity_metrics: List[Dict[str, Any]],
        hotspots: List[Dict[str, Any]],
        language_stats: Dict[str, int],
        file_tree: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        parsed_commits = [self._normalize_commit(c) for c in commits]
        commit_sizes = [c["insertions"] + c["deletions"] for c in parsed_commits]
        commit_sizes_sorted = sorted(commit_sizes)
        total_commits = len(parsed_commits)
        total_changes = sum(commit_sizes)

        hourly = Counter()
        weekday = Counter()
        night_commits = 0
        refactor_candidates = []
        for c in parsed_commits:
            dt = c["committed_at"]
            if dt:
                hourly[dt.hour] += 1
                weekday[dt.strftime("%A")] += 1
                if dt.hour < 6:
                    night_commits += 1
            msg = c["message"].lower()
            if any(k in msg for k in REFACTOR_KEYWORDS):
                refactor_candidates.append(c)

        top_contributors = sorted(
            contributors,
            key=lambda x: _safe_int(x.get("commits"), 0),
            reverse=True,
        )
        contributor_commit_counts = [_safe_int(c.get("commits"), 0) for c in top_contributors]
        bus_factor = self._bus_factor(contributor_commit_counts)

        complexity_values = [
            float(item.get("cyclomatic_complexity", 0) or 0)
            for item in complexity_metrics
            if item.get("cyclomatic_complexity") is not None
        ]
        high_risk_files = [
            item for item in complexity_metrics if float(item.get("cyclomatic_complexity", 0) or 0) >= 15
        ]
        flat_files, directory_count, max_depth = self._flatten_file_tree(file_tree or {})
        total_file_size = sum(int(f.get("size", 0) or 0) for f in flat_files)
        top_large_files = sorted(flat_files, key=lambda x: int(x.get("size", 0) or 0), reverse=True)[:10]

        engineering_signals = self._engineering_signals(flat_files)
        risk_flags = self._risk_flags(
            total_commits=total_commits,
            bus_factor=bus_factor,
            high_risk_file_count=len(high_risk_files),
            engineering_signals=engineering_signals,
        )
        time_machine = self._build_time_machine(parsed_commits)
        blast_radius = self._build_blast_radius(flat_files, hotspots, complexity_metrics)
        health_scorecard = self._health_scorecard(
            total_commits=total_commits,
            bus_factor=bus_factor,
            high_risk_file_count=len(high_risk_files),
            engineering_signals=engineering_signals,
            language_stats=language_stats,
            complexity_scanned=len(complexity_metrics),
            total_files=len(flat_files),
        )
        fingerprint = self._repo_fingerprint(
            engineering_signals=engineering_signals,
            habits={"night_commit_ratio": round((night_commits / total_commits) * 100, 2) if total_commits else 0},
            health_score=health_scorecard["overall_score"],
            language_stats=language_stats,
        )
        collaboration_story = self._collaboration_story(parsed_commits)
        weekly_digest = self._weekly_health_digest(parsed_commits)
        release_readiness = self._release_readiness(
            health_scorecard=health_scorecard,
            risk_flags=risk_flags,
            engineering_signals=engineering_signals,
            team_info={"bus_factor": bus_factor},
            complexity_profile={"high_risk_file_count": len(high_risk_files)},
        )
        archetypes = self._repo_archetypes(
            engineering_signals=engineering_signals,
            health_scorecard=health_scorecard,
            habits={"night_commit_ratio": round((night_commits / total_commits) * 100, 2) if total_commits else 0},
            summary={
                "total_commits": total_commits,
                "avg_changes_per_commit": round(total_changes / total_commits, 2) if total_commits else 0,
                "top_contributor_share_percent": round((contributor_commit_counts[0] / total_commits) * 100, 2)
                if total_commits and contributor_commit_counts
                else 0,
            },
            complexity_profile={"high_risk_file_count": len(high_risk_files)},
        )

        insights = {
            "summary": {
                "total_commits_analyzed": total_commits,
                "total_contributors": len(contributors),
                "total_code_changes": total_changes,
                "avg_changes_per_commit": round(total_changes / total_commits, 2) if total_commits else 0,
            },
            "development_habits": {
                "night_commit_ratio": round((night_commits / total_commits) * 100, 2) if total_commits else 0,
                "most_active_hours": [
                    {"hour": hour, "commits": count}
                    for hour, count in hourly.most_common(5)
                ],
                "most_active_weekdays": [
                    {"day": day, "commits": count}
                    for day, count in weekday.most_common()
                ],
            },
            "team_dynamics": {
                "top_contributors": [
                    {
                        "name": c.get("name") or c.get("email"),
                        "commits": _safe_int(c.get("commits"), 0),
                    }
                    for c in top_contributors[:5]
                ],
                "bus_factor_50_percent": bus_factor,
                "top_contributor_commit_share_percent": round(
                    (contributor_commit_counts[0] / total_commits) * 100, 2
                )
                if total_commits and contributor_commit_counts
                else 0,
            },
            "commit_behavior": {
                "median_changes_per_commit": round(median(commit_sizes_sorted), 2) if commit_sizes_sorted else 0,
                "p90_changes_per_commit": self._percentile(commit_sizes_sorted, 90),
                "largest_commits": [
                    {
                        "sha": c["sha"][:10],
                        "author": c["author_name"],
                        "changes": c["insertions"] + c["deletions"],
                        "message": c["message"][:120],
                    }
                    for c in sorted(
                        parsed_commits,
                        key=lambda x: x["insertions"] + x["deletions"],
                        reverse=True,
                    )[:5]
                ],
            },
            "refactor_signals": {
                "keyword_detected_refactors": len(refactor_candidates),
                "examples": [
                    {
                        "sha": c["sha"][:10],
                        "author": c["author_name"],
                        "message": c["message"][:160],
                    }
                    for c in refactor_candidates[:10]
                ],
            },
            "language_profile": {
                "languages": self._rank_languages(language_stats),
                "dominant_language": max(language_stats, key=language_stats.get) if language_stats else None,
                "language_diversity_index": self._shannon_diversity(language_stats),
            },
            "complexity_profile": {
                "files_scanned": len(complexity_metrics),
                "avg_cyclomatic_complexity": round(sum(complexity_values) / len(complexity_values), 2)
                if complexity_values
                else 0,
                "high_risk_file_count": len(high_risk_files),
                "hotspots": [
                    {
                        "path": h.get("path"),
                        "cyclomatic_complexity": h.get("cyclomatic_complexity"),
                    }
                    for h in hotspots[:10]
                ],
            },
            "repository_structure": {
                "total_files": len(flat_files),
                "total_directories": directory_count,
                "max_depth": max_depth,
                "total_size_bytes": total_file_size,
                "largest_files": [
                    {
                        "path": f.get("path"),
                        "size_bytes": int(f.get("size", 0) or 0),
                    }
                    for f in top_large_files
                ],
                "size_distribution": self._size_distribution(flat_files),
            },
            "engineering_signals": engineering_signals,
            "risk_flags": risk_flags,
            "insight_quality": self._insight_quality(total_commits, len(flat_files), len(complexity_metrics)),
            "time_machine": time_machine,
            "blast_radius": blast_radius,
            "health_scorecard": health_scorecard,
            "repo_fingerprint": fingerprint,
            "collaboration_story": collaboration_story,
            "weekly_health_digest": weekly_digest,
            "release_readiness": release_readiness,
            "repo_archetypes": archetypes,
        }
        insights["executive_summary"] = self._executive_summary(insights)
        return insights

    def _normalize_commit(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        stats = commit.get("stats") or {}
        return {
            "sha": str(commit.get("sha", "")),
            "message": str(commit.get("message", "")),
            "author_name": str(commit.get("author_name", "unknown")),
            "insertions": _safe_int(stats.get("insertions"), 0),
            "deletions": _safe_int(stats.get("deletions"), 0),
            "files_changed": _safe_int(stats.get("files"), 0),
            "committed_at": _parse_datetime(commit.get("committed_at")),
        }

    def _bus_factor(self, commit_counts: List[int]) -> int:
        total = sum(commit_counts)
        if total <= 0:
            return 0
        running = 0
        people = 0
        for count in commit_counts:
            running += count
            people += 1
            if running / total >= 0.5:
                return people
        return people

    def _percentile(self, values: List[int], percentile: int) -> float:
        if not values:
            return 0
        if len(values) == 1:
            return float(values[0])
        idx = int((percentile / 100) * (len(values) - 1))
        return float(values[idx])

    def _rank_languages(self, language_stats: Dict[str, int]) -> List[Dict[str, Any]]:
        total = sum(language_stats.values())
        ranked = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "language": ext,
                "files": count,
                "share_percent": round((count / total) * 100, 2) if total else 0,
            }
            for ext, count in ranked
        ]

    def _flatten_file_tree(self, root: Dict[str, Any]) -> tuple[list[Dict[str, Any]], int, int]:
        files: list[Dict[str, Any]] = []
        directory_count = 0
        max_depth = 0

        def walk(node: Dict[str, Any], depth: int):
            nonlocal directory_count, max_depth
            max_depth = max(max_depth, depth)
            node_type = node.get("type")
            if node_type == "directory":
                directory_count += 1
                for child in node.get("children", []):
                    if isinstance(child, dict):
                        walk(child, depth + 1)
            elif node_type == "file":
                files.append(node)

        if root:
            walk(root, 0)
        return files, max(0, directory_count - 1), max_depth

    def _size_distribution(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        buckets = {
            "<10KB": 0,
            "10KB-100KB": 0,
            "100KB-1MB": 0,
            ">1MB": 0,
        }
        for f in files:
            size = int(f.get("size", 0) or 0)
            if size < 10 * 1024:
                buckets["<10KB"] += 1
            elif size < 100 * 1024:
                buckets["10KB-100KB"] += 1
            elif size < 1024 * 1024:
                buckets["100KB-1MB"] += 1
            else:
                buckets[">1MB"] += 1
        return [{"bucket": k, "files": v} for k, v in buckets.items()]

    def _engineering_signals(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        paths = [str(f.get("path", "")).lower() for f in files]
        has_tests = any("/test" in p or p.startswith("test") or "tests/" in p for p in paths)
        has_ci = any(".github/workflows/" in p or ".gitlab-ci" in p or "jenkinsfile" in p for p in paths)
        has_docker = any("dockerfile" in p or "docker-compose" in p for p in paths)
        has_docs = any(p.startswith("docs/") or p.endswith("readme.md") for p in paths)
        notebook_count = sum(1 for p in paths if p.endswith(".ipynb"))
        config_count = sum(
            1
            for p in paths
            if p.endswith((".json", ".yaml", ".yml", ".toml", ".ini"))
        )
        return {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_docker": has_docker,
            "has_docs": has_docs,
            "notebook_count": notebook_count,
            "config_file_count": config_count,
        }

    def _risk_flags(
        self,
        total_commits: int,
        bus_factor: int,
        high_risk_file_count: int,
        engineering_signals: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        flags: List[Dict[str, str]] = []
        if bus_factor <= 1 and total_commits > 20:
            flags.append({"severity": "high", "message": "High ownership concentration (bus factor <= 1)."})
        if high_risk_file_count > 20:
            flags.append({"severity": "high", "message": "Large number of high-complexity files detected."})
        if not engineering_signals.get("has_tests"):
            flags.append({"severity": "medium", "message": "No obvious test structure detected."})
        if not engineering_signals.get("has_ci"):
            flags.append({"severity": "medium", "message": "No CI workflow detected."})
        if total_commits < 10:
            flags.append({"severity": "low", "message": "Limited commit history; behavior insights have low confidence."})
        return flags

    def _insight_quality(self, total_commits: int, total_files: int, complexity_scanned: int) -> Dict[str, Any]:
        confidence = 100
        notes = []
        if total_commits < 30:
            confidence -= 25
            notes.append("Low commit history reduces behavior signal quality.")
        if total_files > 0 and complexity_scanned < int(total_files * 0.2):
            confidence -= 20
            notes.append("Complexity scan covered a limited subset of files.")
        if total_files < 20:
            confidence -= 10
            notes.append("Small codebase size limits structural signal richness.")
        return {"confidence_score": max(0, confidence), "notes": notes}

    def _shannon_diversity(self, language_stats: Dict[str, int]) -> float:
        total = sum(language_stats.values())
        if total <= 0:
            return 0.0
        entropy = 0.0
        for count in language_stats.values():
            p = count / total
            entropy -= p * math.log2(p) if p > 0 else 0
        return round(entropy, 3)

    def _build_time_machine(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        ordered = sorted(
            [x for x in commits if x.get("committed_at")],
            key=lambda x: x["committed_at"],
        )
        daily: Dict[str, Dict[str, Any]] = {}
        for c in ordered:
            date_key = c["committed_at"].date().isoformat()
            point = daily.setdefault(
                date_key,
                {
                    "date": date_key,
                    "day_commits": 0,
                    "day_changes": 0,
                    "authors": Counter(),
                    "commit_sha": "",
                },
            )
            changes = int(c.get("insertions", 0) or 0) + int(c.get("deletions", 0) or 0)
            point["day_commits"] += 1
            point["day_changes"] += changes
            point["authors"][c.get("author_name") or "unknown"] += 1
            point["commit_sha"] = str(c.get("sha", ""))[:10]

        timeline = []
        cumulative_commits = 0
        cumulative_changes = 0
        rolling_commits: List[int] = []
        rolling_changes: List[int] = []
        for date_key in sorted(daily.keys()):
            day_point = daily[date_key]
            cumulative_commits += int(day_point["day_commits"])
            cumulative_changes += int(day_point["day_changes"])
            rolling_commits.append(int(day_point["day_commits"]))
            rolling_changes.append(int(day_point["day_changes"]))
            if len(rolling_commits) > 7:
                rolling_commits.pop(0)
            if len(rolling_changes) > 7:
                rolling_changes.pop(0)

            lead_author = day_point["authors"].most_common(1)[0][0] if day_point["authors"] else "unknown"
            timeline.append(
                {
                    "date": date_key,
                    "commit_sha": day_point["commit_sha"],
                    "author": lead_author,
                    "day_commits": int(day_point["day_commits"]),
                    "day_changes": int(day_point["day_changes"]),
                    "unique_authors": len(day_point["authors"]),
                    "rolling_7d_commits": int(sum(rolling_commits)),
                    "rolling_7d_changes": int(sum(rolling_changes)),
                    "cumulative_commits": cumulative_commits,
                    "cumulative_changes": cumulative_changes,
                }
            )

        if len(timeline) > 250:
            step = max(1, len(timeline) // 250)
            timeline = timeline[::step]
        return {
            "points": timeline,
            "window_start": timeline[0]["date"] if timeline else None,
            "window_end": timeline[-1]["date"] if timeline else None,
        }

    def _build_blast_radius(
        self,
        files: List[Dict[str, Any]],
        hotspots: List[Dict[str, Any]],
        complexity_metrics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        complexity_by_path = {
            str(item.get("path")): float(item.get("cyclomatic_complexity", 0) or 0)
            for item in complexity_metrics
        }
        files_by_dir: Dict[str, int] = {}
        for f in files:
            path = str(f.get("path", ""))
            directory = path.rsplit("/", 1)[0] if "/" in path else "."
            files_by_dir[directory] = files_by_dir.get(directory, 0) + 1

        candidates = []
        base_candidates = hotspots[:15] if hotspots else [
            {"path": f.get("path"), "cyclomatic_complexity": complexity_by_path.get(str(f.get("path")), 0)}
            for f in sorted(files, key=lambda x: int(x.get("size", 0) or 0), reverse=True)[:15]
        ]
        for item in base_candidates:
            path = str(item.get("path", ""))
            directory = path.rsplit("/", 1)[0] if "/" in path else "."
            complexity = float(item.get("cyclomatic_complexity", complexity_by_path.get(path, 0)) or 0)
            size = 0
            for f in files:
                if str(f.get("path")) == path:
                    size = int(f.get("size", 0) or 0)
                    break
            neighbor_files = files_by_dir.get(directory, 1)
            impact_score = round(min(100.0, complexity * 2.2 + math.log2(size + 2) * 3 + neighbor_files * 0.25), 2)
            candidates.append(
                {
                    "path": path,
                    "directory": directory,
                    "estimated_neighbor_files": neighbor_files,
                    "complexity": round(complexity, 2),
                    "size_bytes": size,
                    "impact_score": impact_score,
                    "risk_tier": "high" if impact_score >= 70 else "medium" if impact_score >= 40 else "low",
                }
            )
        candidates = sorted(candidates, key=lambda x: x["impact_score"], reverse=True)[:20]
        return {"candidates": candidates}

    def _health_scorecard(
        self,
        total_commits: int,
        bus_factor: int,
        high_risk_file_count: int,
        engineering_signals: Dict[str, Any],
        language_stats: Dict[str, int],
        complexity_scanned: int,
        total_files: int,
    ) -> Dict[str, Any]:
        ownership = min(100, 20 + bus_factor * 8)
        reliability = 100
        if not engineering_signals.get("has_tests"):
            reliability -= 30
        if not engineering_signals.get("has_ci"):
            reliability -= 20
        if not engineering_signals.get("has_docs"):
            reliability -= 10
        complexity_risk = max(0, 100 - high_risk_file_count * 4)
        data_coverage = 100
        if total_files > 0:
            coverage_ratio = complexity_scanned / total_files
            if coverage_ratio < 0.2:
                data_coverage -= 40
            elif coverage_ratio < 0.5:
                data_coverage -= 20
        velocity = 100 if total_commits >= 200 else max(30, int(total_commits / 2))
        architecture = min(100, 40 + int(self._shannon_diversity(language_stats) * 20))

        dimensions = {
            "ownership_resilience": max(0, ownership),
            "delivery_reliability": max(0, reliability),
            "complexity_health": max(0, complexity_risk),
            "analysis_coverage": max(0, data_coverage),
            "engineering_velocity": max(0, velocity),
            "architecture_balance": max(0, architecture),
        }
        overall = round(
            dimensions["ownership_resilience"] * 0.18
            + dimensions["delivery_reliability"] * 0.22
            + dimensions["complexity_health"] * 0.2
            + dimensions["analysis_coverage"] * 0.12
            + dimensions["engineering_velocity"] * 0.14
            + dimensions["architecture_balance"] * 0.14,
            2,
        )
        return {"overall_score": overall, "dimensions": dimensions}

    def _repo_fingerprint(
        self,
        engineering_signals: Dict[str, Any],
        habits: Dict[str, Any],
        health_score: float,
        language_stats: Dict[str, int],
    ) -> Dict[str, Any]:
        labels = []
        dominant = max(language_stats, key=language_stats.get) if language_stats else "unknown"
        labels.append(f"Dominant language family: {dominant}")
        if habits.get("night_commit_ratio", 0) >= 25:
            labels.append("Night-Shift Builders")
        elif habits.get("night_commit_ratio", 0) <= 8:
            labels.append("Daylight Delivery Team")
        if engineering_signals.get("has_tests") and engineering_signals.get("has_ci"):
            labels.append("Quality-Guarded Pipeline")
        if engineering_signals.get("notebook_count", 0) > 0:
            labels.append("Exploration + Product Blend")
        if health_score >= 85:
            labels.append("Operationally Mature Codebase")
        elif health_score < 60:
            labels.append("Refactor Opportunity Zone")
        return {"labels": labels[:6], "tagline": " | ".join(labels[:3])}

    def _collaboration_story(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        ordered = sorted(
            [x for x in commits if x.get("committed_at")],
            key=lambda x: x["committed_at"],
        )
        if not ordered:
            return {
                "headline": "No collaboration timeline available.",
                "collaboration_index": 0,
                "metrics": {
                    "active_contributors": 0,
                    "handoff_events": 0,
                    "cross_author_handoffs": 0,
                },
                "top_handoffs": [],
                "contributor_bands": [],
                "weekly_collaboration": [],
                "narrative": ["No commit history was available to infer collaboration behavior."],
            }

        author_counts = Counter((c.get("author_name") or "unknown") for c in ordered)
        total_commits = len(ordered)
        handoff_pairs: Counter[tuple[str, str]] = Counter()
        weekly_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"commits": 0, "changes": 0, "contributors": set(), "handoffs": 0}
        )

        previous = None
        for c in ordered:
            week_key = c["committed_at"].strftime("%G-W%V")
            bucket = weekly_data[week_key]
            bucket["commits"] += 1
            bucket["changes"] += int(c.get("insertions", 0) or 0) + int(c.get("deletions", 0) or 0)
            bucket["contributors"].add(c.get("author_name") or "unknown")
            if previous and previous.get("author_name") != c.get("author_name"):
                elapsed_hours = (c["committed_at"] - previous["committed_at"]).total_seconds() / 3600
                if elapsed_hours <= 72:
                    pair = (previous.get("author_name") or "unknown", c.get("author_name") or "unknown")
                    handoff_pairs[pair] += 1
                    bucket["handoffs"] += 1
            previous = c

        top_handoffs = [
            {"from": source, "to": target, "count": count}
            for (source, target), count in handoff_pairs.most_common(6)
        ]
        handoff_events = sum(handoff_pairs.values())
        top_author_share = (author_counts.most_common(1)[0][1] / total_commits) * 100 if total_commits else 0
        collaboration_index = round(
            min(
                100.0,
                (100 - top_author_share) * 0.55
                + (min(100.0, (handoff_events / max(1, total_commits - 1)) * 120)) * 0.45,
            ),
            2,
        )

        weekly_collaboration = []
        for week_key in sorted(weekly_data.keys())[-16:]:
            bucket = weekly_data[week_key]
            commits_in_week = int(bucket["commits"])
            contributors_in_week = len(bucket["contributors"])
            handoffs_in_week = int(bucket["handoffs"])
            density = round((handoffs_in_week / max(1, commits_in_week - 1)) * 100, 2)
            weekly_collaboration.append(
                {
                    "week": week_key,
                    "commits": commits_in_week,
                    "contributors": contributors_in_week,
                    "handoffs": handoffs_in_week,
                    "handoff_density_percent": density,
                }
            )

        contributor_bands = []
        for name, commits_count in author_counts.most_common(10):
            share = round((commits_count / total_commits) * 100, 2) if total_commits else 0
            if share >= 20:
                band = "core"
            elif share >= 8:
                band = "active"
            else:
                band = "support"
            contributor_bands.append(
                {
                    "name": name,
                    "commits": commits_count,
                    "share_percent": share,
                    "band": band,
                }
            )

        if collaboration_index >= 70:
            headline = "Cross-team collaboration is healthy and distributed."
        elif collaboration_index >= 45:
            headline = "Collaboration is moderate; ownership is somewhat concentrated."
        else:
            headline = "Collaboration is concentrated; knowledge-sharing risk is elevated."

        narrative = [
            f"{len(author_counts)} contributors participated, with {handoff_events} near-term cross-author handoffs.",
            f"Top contributor share is {round(top_author_share, 2)}%, driving a collaboration index of {collaboration_index}.",
        ]
        if top_handoffs:
            top = top_handoffs[0]
            narrative.append(
                f"Most frequent handoff path: {top['from']} -> {top['to']} ({top['count']} transitions)."
            )

        return {
            "headline": headline,
            "collaboration_index": collaboration_index,
            "metrics": {
                "active_contributors": len(author_counts),
                "handoff_events": handoff_events,
                "cross_author_handoffs": handoff_events,
            },
            "top_handoffs": top_handoffs,
            "contributor_bands": contributor_bands,
            "weekly_collaboration": weekly_collaboration,
            "narrative": narrative,
        }

    def _weekly_health_digest(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        ordered = sorted(
            [x for x in commits if x.get("committed_at")],
            key=lambda x: x["committed_at"],
        )
        if not ordered:
            return {
                "latest_week": None,
                "weeks": [],
                "latest": {},
                "trend": {},
                "highlights": ["No weekly digest available without commit timestamps."],
            }

        weekly: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "commits": 0,
                "changes": 0,
                "night_commits": 0,
                "refactor_commits": 0,
                "contributors": set(),
            }
        )
        for c in ordered:
            week_key = c["committed_at"].strftime("%G-W%V")
            bucket = weekly[week_key]
            bucket["commits"] += 1
            bucket["changes"] += int(c.get("insertions", 0) or 0) + int(c.get("deletions", 0) or 0)
            bucket["contributors"].add(c.get("author_name") or "unknown")
            if c["committed_at"].hour < 6:
                bucket["night_commits"] += 1
            message = str(c.get("message", "")).lower()
            if any(keyword in message for keyword in REFACTOR_KEYWORDS):
                bucket["refactor_commits"] += 1

        weeks = []
        for week_key in sorted(weekly.keys())[-16:]:
            bucket = weekly[week_key]
            commits_in_week = int(bucket["commits"])
            changes_in_week = int(bucket["changes"])
            weeks.append(
                {
                    "week": week_key,
                    "commits": commits_in_week,
                    "changes": changes_in_week,
                    "contributors": len(bucket["contributors"]),
                    "avg_changes_per_commit": round(changes_in_week / commits_in_week, 2) if commits_in_week else 0,
                    "night_commit_ratio": round((bucket["night_commits"] / commits_in_week) * 100, 2)
                    if commits_in_week
                    else 0,
                    "refactor_commits": int(bucket["refactor_commits"]),
                }
            )

        latest = weeks[-1]
        previous = weeks[-2] if len(weeks) > 1 else None

        def _delta_pct(current: float, prev: float) -> float:
            if prev == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - prev) / prev) * 100, 2)

        trend = {
            "commit_delta_percent": _delta_pct(latest["commits"], previous["commits"]) if previous else 0.0,
            "change_delta_percent": _delta_pct(latest["changes"], previous["changes"]) if previous else 0.0,
            "contributor_delta": (latest["contributors"] - previous["contributors"]) if previous else 0,
            "night_ratio_delta": round(latest["night_commit_ratio"] - previous["night_commit_ratio"], 2)
            if previous
            else 0.0,
        }

        if trend["commit_delta_percent"] >= 10 and trend["night_ratio_delta"] <= 5:
            momentum = "improving"
        elif trend["commit_delta_percent"] <= -15 or trend["night_ratio_delta"] >= 10:
            momentum = "watch"
        else:
            momentum = "stable"
        trend["momentum"] = momentum

        highlights = [
            f"Latest week {latest['week']}: {latest['commits']} commits, {latest['contributors']} active contributors.",
            f"Week-over-week commit delta: {trend['commit_delta_percent']}% and change delta: {trend['change_delta_percent']}%.",
            f"Night-commit ratio is {latest['night_commit_ratio']}% ({trend['night_ratio_delta']}% delta vs previous week).",
        ]
        if latest["refactor_commits"] > 0:
            highlights.append(f"Refactor-tagged commits this week: {latest['refactor_commits']}.")

        return {
            "latest_week": latest["week"],
            "weeks": weeks,
            "latest": latest,
            "trend": trend,
            "highlights": highlights,
        }

    def _release_readiness(
        self,
        health_scorecard: Dict[str, Any],
        risk_flags: List[Dict[str, Any]],
        engineering_signals: Dict[str, Any],
        team_info: Dict[str, Any],
        complexity_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        dimensions = health_scorecard.get("dimensions", {})
        base_score = float(health_scorecard.get("overall_score", 0) or 0)
        bus_factor = int(team_info.get("bus_factor", 0) or 0)
        high_risk_file_count = int(complexity_profile.get("high_risk_file_count", 0) or 0)

        severity_counts = {
            "high": sum(1 for flag in risk_flags if flag.get("severity") == "high"),
            "medium": sum(1 for flag in risk_flags if flag.get("severity") == "medium"),
            "low": sum(1 for flag in risk_flags if flag.get("severity") == "low"),
        }

        score = base_score
        score -= severity_counts["high"] * 12
        score -= severity_counts["medium"] * 6
        score -= severity_counts["low"] * 2
        if not engineering_signals.get("has_tests"):
            score -= 15
        if not engineering_signals.get("has_ci"):
            score -= 15
        if bus_factor <= 1:
            score -= 12
        elif bus_factor <= 2:
            score -= 6
        if high_risk_file_count >= 20:
            score -= 15
        elif high_risk_file_count >= 10:
            score -= 8

        score = round(max(0.0, min(100.0, score)), 2)

        def _gate(name: str, status: str, detail: str) -> Dict[str, str]:
            return {"name": name, "status": status, "detail": detail}

        gates = [
            _gate(
                "Test Signal",
                "pass" if engineering_signals.get("has_tests") else "fail",
                "Tests detected" if engineering_signals.get("has_tests") else "No clear test directory detected",
            ),
            _gate(
                "CI Pipeline",
                "pass" if engineering_signals.get("has_ci") else "fail",
                "CI workflow detected" if engineering_signals.get("has_ci") else "No CI workflow detected",
            ),
            _gate(
                "Ownership Resilience",
                "pass" if bus_factor >= 3 else "warn" if bus_factor == 2 else "fail",
                f"Bus factor(50%) = {bus_factor}",
            ),
            _gate(
                "Complexity Pressure",
                "pass" if high_risk_file_count <= 5 else "warn" if high_risk_file_count <= 15 else "fail",
                f"{high_risk_file_count} high-risk files",
            ),
            _gate(
                "Delivery Reliability",
                "pass"
                if float(dimensions.get("delivery_reliability", 0) or 0) >= 75
                else "warn"
                if float(dimensions.get("delivery_reliability", 0) or 0) >= 55
                else "fail",
                f"Score {round(float(dimensions.get('delivery_reliability', 0) or 0), 2)}",
            ),
        ]

        blockers = [flag.get("message", "") for flag in risk_flags if flag.get("severity") == "high"]
        blockers += [gate["name"] + ": " + gate["detail"] for gate in gates if gate["status"] == "fail"]
        blockers = [b for b in blockers if b][:8]

        if score >= 85:
            tier = "ready"
            recommendation = "Release posture is strong. Maintain current guardrails and monitor regressions."
        elif score >= 70:
            tier = "stabilizing"
            recommendation = "Near-ready. Address failing gates before broad rollout."
        elif score >= 55:
            tier = "hardening"
            recommendation = "Needs hardening. Prioritize tests/CI and ownership resilience."
        else:
            tier = "not_ready"
            recommendation = "Block release. Resolve critical risk flags and failing quality gates."

        recommendations = [
            recommendation,
            "Reduce high-complexity hotspots in frequently changed modules." if high_risk_file_count > 10 else "Keep complexity hotspots under active review.",
            "Increase contributor overlap to reduce ownership concentration." if bus_factor <= 2 else "Preserve cross-team code ownership patterns.",
        ]

        return {
            "score": score,
            "tier": tier,
            "ship_confidence": int(round(score)),
            "severity_counts": severity_counts,
            "gates": gates,
            "blockers": blockers,
            "recommendations": recommendations,
        }

    def _repo_archetypes(
        self,
        engineering_signals: Dict[str, Any],
        health_scorecard: Dict[str, Any],
        habits: Dict[str, Any],
        summary: Dict[str, Any],
        complexity_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        badges: List[Dict[str, Any]] = []
        delivery_reliability = float(health_scorecard.get("dimensions", {}).get("delivery_reliability", 0) or 0)
        ownership_resilience = float(health_scorecard.get("dimensions", {}).get("ownership_resilience", 0) or 0)
        complexity_health = float(health_scorecard.get("dimensions", {}).get("complexity_health", 0) or 0)
        night_ratio = float(habits.get("night_commit_ratio", 0) or 0)
        total_commits = int(summary.get("total_commits", 0) or 0)
        avg_changes = float(summary.get("avg_changes_per_commit", 0) or 0)
        top_share = float(summary.get("top_contributor_share_percent", 0) or 0)
        high_risk_files = int(complexity_profile.get("high_risk_file_count", 0) or 0)

        def add_badge(name: str, tier: str, confidence: float, reason: str):
            badges.append(
                {
                    "name": name,
                    "tier": tier,
                    "confidence": int(round(max(0, min(100, confidence)))),
                    "reason": reason,
                }
            )

        if engineering_signals.get("has_tests") and engineering_signals.get("has_ci"):
            add_badge(
                "Quality Gatekeepers",
                "strong",
                70 + delivery_reliability * 0.25,
                "Repository shows tests and CI workflow coverage.",
            )
        if night_ratio <= 10:
            add_badge(
                "Daylight Delivery Crew",
                "emerging",
                65 + max(0.0, 10 - night_ratio) * 2,
                "Most work lands during standard collaboration windows.",
            )
        if night_ratio >= 25:
            add_badge(
                "Night Shift Builders",
                "emerging",
                min(95, 60 + night_ratio),
                "A substantial share of commits land late night.",
            )
        if total_commits >= 500 and avg_changes >= 80:
            add_badge(
                "Velocity Engine",
                "strong",
                min(96, 55 + (total_commits / 40) + (avg_changes / 6)),
                "High commit volume and substantial per-commit changes suggest strong throughput.",
            )
        if high_risk_files <= 5 and complexity_health >= 75:
            add_badge(
                "Refactor Ready",
                "strong",
                70 + complexity_health * 0.2,
                "Complexity hotspots are contained for safe refactors.",
            )
        if top_share >= 60:
            add_badge(
                "Single-Threaded Core",
                "risk",
                min(95, 60 + (top_share - 60) * 1.5),
                "One contributor owns the majority of commits, creating concentration risk.",
            )
        if top_share <= 30 and ownership_resilience >= 65:
            add_badge(
                "Shared Ownership Guild",
                "strong",
                65 + ownership_resilience * 0.25,
                "Ownership is distributed across contributors with healthy resilience.",
            )
        if engineering_signals.get("has_docs"):
            add_badge(
                "Docs-Aware Builders",
                "emerging",
                60 + (10 if engineering_signals.get("has_tests") else 0),
                "Documentation artifacts are present in the codebase.",
            )

        if not badges:
            add_badge(
                "Emerging Codebase",
                "emerging",
                max(30, health_scorecard.get("overall_score", 0)),
                "Repository signals are still forming; more history will sharpen characterization.",
            )

        badges = sorted(badges, key=lambda x: x["confidence"], reverse=True)[:6]
        primary = badges[0]["name"]
        storyline = f"{primary} with {len(badges)} detected engineering archetype signal(s)."
        return {
            "primary": primary,
            "badges": badges,
            "storyline": storyline,
        }

    def _executive_summary(self, insights: Dict[str, Any]) -> List[str]:
        summary = insights["summary"]
        habits = insights["development_habits"]
        team = insights["team_dynamics"]
        complexity = insights["complexity_profile"]
        structure = insights["repository_structure"]
        quality = insights["insight_quality"]
        collaboration = insights.get("collaboration_story", {})
        readiness = insights.get("release_readiness", {})

        lines = [
            f"Analyzed {summary['total_commits_analyzed']} commits across {summary['total_contributors']} contributors.",
            f"Top contributor owns {team['top_contributor_commit_share_percent']}% of commits; bus factor(50%) is {team['bus_factor_50_percent']}.",
            f"Night-time commit ratio is {habits['night_commit_ratio']}%, revealing delivery-window habits.",
            f"Detected {complexity['high_risk_file_count']} high-risk files by cyclomatic complexity.",
            f"Repository shape: {structure['total_files']} files across {structure['total_directories']} directories (depth {structure['max_depth']}).",
            f"Insight confidence score: {quality['confidence_score']}/100.",
        ]
        if readiness:
            lines.append(
                f"Release readiness is {readiness.get('score', 0)}/100 ({str(readiness.get('tier', 'unknown')).upper()})."
            )
        if collaboration:
            lines.append(
                f"Collaboration index is {collaboration.get('collaboration_index', 0)} with {collaboration.get('metrics', {}).get('handoff_events', 0)} cross-author handoffs."
            )
        if complexity["hotspots"]:
            top = complexity["hotspots"][0]
            lines.append(
                f"Top hotspot: {top.get('path')} (complexity={top.get('cyclomatic_complexity')})."
            )
        return lines
