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


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


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
        anomaly_detective = self._anomaly_detective(parsed_commits)
        bus_factor_shock_test = self._bus_factor_shock_test(top_contributors, total_commits)
        engineering_weather_forecast = self._engineering_weather_forecast(
            weekly_digest=weekly_digest,
            risk_flags=risk_flags,
            release_readiness=release_readiness,
            anomaly_report=anomaly_detective,
            health_scorecard=health_scorecard,
        )
        pr_pre_mortem = self._pr_pre_mortem_simulator(
            blast_radius=blast_radius,
            hotspots=hotspots,
            top_contributors=top_contributors,
            engineering_signals=engineering_signals,
        )
        ai_action_briefs = self._ai_action_briefs(
            pre_mortem=pr_pre_mortem,
            bus_factor_shock=bus_factor_shock_test,
            engineering_forecast=engineering_weather_forecast,
            anomaly_report=anomaly_detective,
            release_readiness=release_readiness,
            risk_flags=risk_flags,
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
            "pr_pre_mortem": pr_pre_mortem,
            "bus_factor_shock_test": bus_factor_shock_test,
            "engineering_weather_forecast": engineering_weather_forecast,
            "anomaly_detective": anomaly_detective,
            "ai_action_briefs": ai_action_briefs,
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

    def _anomaly_detective(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        ordered = sorted(
            [x for x in commits if x.get("committed_at")],
            key=lambda x: x["committed_at"],
        )
        if not ordered:
            return {
                "risk_index": 0,
                "anomaly_count": 0,
                "anomaly_rate_percent": 0.0,
                "counts_by_type": [],
                "highlights": [],
                "recommended_checks": ["No anomalies available without commit history."],
            }

        commit_sizes = sorted(
            int(c.get("insertions", 0) or 0) + int(c.get("deletions", 0) or 0)
            for c in ordered
        )
        files_changed = sorted(int(c.get("files_changed", 0) or 0) for c in ordered)
        p90_changes = self._percentile(commit_sizes, 90)
        p95_changes = self._percentile(commit_sizes, 95)
        p95_files = self._percentile(files_changed, 95)

        daily_buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for commit in ordered:
            day_key = commit["committed_at"].date().isoformat()
            daily_buckets[day_key].append(commit)

        daily_commit_counts = [len(items) for items in daily_buckets.values()]
        median_daily_commits = float(median(daily_commit_counts)) if daily_commit_counts else 1.0
        anomalies: List[Dict[str, Any]] = []

        def _add_anomaly(
            anomaly_type: str,
            severity: str,
            score: float,
            headline: str,
            detail: str,
            commit: Dict[str, Any] | None = None,
            day: str | None = None,
        ):
            item = {
                "type": anomaly_type,
                "severity": severity,
                "score": round(score, 2),
                "headline": headline,
                "detail": detail,
                "date": day or (commit["committed_at"].date().isoformat() if commit else None),
            }
            if commit:
                item["commit_sha"] = str(commit.get("sha", ""))[:10]
                item["author"] = commit.get("author_name") or "unknown"
                item["changes"] = int(commit.get("insertions", 0) or 0) + int(commit.get("deletions", 0) or 0)
            anomalies.append(item)

        for commit in ordered:
            dt = commit["committed_at"]
            message = str(commit.get("message", "")).lower()
            changes = int(commit.get("insertions", 0) or 0) + int(commit.get("deletions", 0) or 0)
            files = int(commit.get("files_changed", 0) or 0)

            if changes >= max(500, p95_changes * 1.8):
                _add_anomaly(
                    anomaly_type="mega_commit",
                    severity="high" if changes >= max(1200, p95_changes * 2.3) else "medium",
                    score=min(100.0, 55 + (changes / max(1.0, p90_changes + 1)) * 16),
                    headline="Large commit spike",
                    detail=f"Commit changed {changes} lines in one push.",
                    commit=commit,
                )

            if dt.hour < 5 and changes >= max(220, p90_changes * 1.35):
                _add_anomaly(
                    anomaly_type="off_hours_heavy_change",
                    severity="medium",
                    score=min(100.0, 45 + (changes / max(1.0, p90_changes + 1)) * 10),
                    headline="Large off-hours commit",
                    detail=f"Heavy change landed at {dt.hour:02d}:00, increasing review risk.",
                    commit=commit,
                )

            if files >= max(35, p95_files * 1.5):
                _add_anomaly(
                    anomaly_type="wide_surface_area",
                    severity="high" if files >= 80 else "medium",
                    score=min(100.0, 50 + files * 0.7),
                    headline="Wide-surface change",
                    detail=f"Commit touched {files} files, which can hide regressions.",
                    commit=commit,
                )

            if ("revert" in message or "hotfix" in message) and changes >= max(80, p90_changes * 0.75):
                _add_anomaly(
                    anomaly_type="stability_event",
                    severity="medium",
                    score=min(100.0, 42 + changes * 0.05),
                    headline="Stability-related high-change commit",
                    detail="Revert/hotfix keyword appears in a relatively large commit.",
                    commit=commit,
                )

        for day, day_commits in daily_buckets.items():
            if len(day_commits) >= max(8, int(math.ceil(median_daily_commits * 3))):
                largest_commit = max(
                    day_commits,
                    key=lambda x: int(x.get("insertions", 0) or 0) + int(x.get("deletions", 0) or 0),
                )
                _add_anomaly(
                    anomaly_type="daily_burst",
                    severity="medium",
                    score=min(100.0, 40 + len(day_commits) * 4.5),
                    headline="Burst activity day",
                    detail=f"{len(day_commits)} commits landed on {day}, far above baseline cadence.",
                    commit=largest_commit,
                    day=day,
                )

        for previous, current in zip(ordered, ordered[1:]):
            gap_days = (current["committed_at"] - previous["committed_at"]).days
            if gap_days >= 14:
                _add_anomaly(
                    anomaly_type="long_gap",
                    severity="low" if gap_days < 30 else "medium",
                    score=min(100.0, 20 + gap_days * 1.2),
                    headline="Long inactivity gap",
                    detail=f"Detected a {gap_days}-day delivery gap between commits.",
                    commit=current,
                )

        severity_rank = {"high": 3, "medium": 2, "low": 1}
        anomalies = sorted(
            anomalies,
            key=lambda item: (severity_rank.get(str(item.get("severity")), 0), float(item.get("score", 0))),
            reverse=True,
        )

        type_counter = Counter(str(item.get("type", "unknown")) for item in anomalies)
        high_count = sum(1 for item in anomalies if item.get("severity") == "high")
        medium_count = sum(1 for item in anomalies if item.get("severity") == "medium")
        low_count = sum(1 for item in anomalies if item.get("severity") == "low")
        anomaly_rate = round((len(anomalies) / max(1, len(ordered))) * 100, 2)
        risk_index = round(
            _clamp(
                high_count * 12 + medium_count * 6 + low_count * 2 + anomaly_rate * 1.2,
                0.0,
                100.0,
            ),
            2,
        )

        recommendations = []
        if high_count > 0:
            recommendations.append("Require peer review and regression tests for high-change commits.")
        if type_counter.get("off_hours_heavy_change", 0) > 0:
            recommendations.append("Introduce scheduled review windows for off-hours high-risk commits.")
        if type_counter.get("wide_surface_area", 0) > 0:
            recommendations.append("Split broad changes into staged pull requests by directory boundary.")
        if not recommendations:
            recommendations.append("No major anomalies detected; keep existing review discipline.")

        return {
            "risk_index": risk_index,
            "anomaly_count": len(anomalies),
            "anomaly_rate_percent": anomaly_rate,
            "counts_by_type": [
                {"type": anomaly_type, "label": anomaly_type.replace("_", " "), "count": count}
                for anomaly_type, count in type_counter.most_common()
            ],
            "highlights": anomalies[:15],
            "recommended_checks": recommendations,
        }

    def _bus_factor_shock_test(
        self,
        top_contributors: List[Dict[str, Any]],
        total_commits: int,
    ) -> Dict[str, Any]:
        contributor_rows = []
        for contributor in top_contributors:
            commits_count = _safe_int(contributor.get("commits"), 0)
            if commits_count <= 0:
                continue
            contributor_rows.append(
                {
                    "name": contributor.get("name") or contributor.get("email") or "unknown",
                    "commits": commits_count,
                }
            )

        if not contributor_rows:
            return {
                "baseline_bus_factor_50_percent": 0,
                "resilience_score": 0,
                "single_point_of_failure": False,
                "scenarios": [],
            }

        effective_total = max(total_commits, sum(item["commits"] for item in contributor_rows))
        baseline_bus_factor = self._bus_factor([item["commits"] for item in contributor_rows])
        top_share = round((contributor_rows[0]["commits"] / max(1, effective_total)) * 100, 2)
        max_removals = min(5, len(contributor_rows))
        scenarios = []

        for removed_count in range(1, max_removals + 1):
            removed = contributor_rows[:removed_count]
            remaining = contributor_rows[removed_count:]
            removed_commits = sum(item["commits"] for item in removed)
            remaining_commits = max(0, effective_total - removed_commits)
            coverage_lost_percent = round((removed_commits / max(1, effective_total)) * 100, 2)
            remaining_bus_factor = self._bus_factor([item["commits"] for item in remaining])
            top_remaining_share = (
                round((remaining[0]["commits"] / max(1, remaining_commits)) * 100, 2)
                if remaining
                else 100.0
            )
            resilience_score = round(
                _clamp(
                    100
                    - (
                        coverage_lost_percent * 0.62
                        + max(0.0, 55 - remaining_bus_factor * 14)
                        + max(0.0, top_remaining_share - 35) * 0.45
                    ),
                    0.0,
                    100.0,
                ),
                2,
            )
            risk_tier = (
                "critical"
                if resilience_score < 35
                else "high"
                if resilience_score < 55
                else "moderate"
                if resilience_score < 75
                else "low"
            )

            per_person_capacity = (remaining_commits / max(1, len(remaining))) if remaining else 0.0
            recovery_days = (
                int(round(max(2.0, (removed_commits / max(1.0, per_person_capacity)) * 3.0)))
                if remaining
                else 30
            )

            scenarios.append(
                {
                    "removed_contributors": [item["name"] for item in removed],
                    "removed_count": removed_count,
                    "coverage_lost_percent": coverage_lost_percent,
                    "coverage_remaining_percent": round(100 - coverage_lost_percent, 2),
                    "new_bus_factor_50_percent": remaining_bus_factor,
                    "top_remaining_share_percent": top_remaining_share,
                    "resilience_score": resilience_score,
                    "risk_tier": risk_tier,
                    "recovery_days_estimate": recovery_days,
                }
            )

        resilience_baseline = round(
            sum(item["resilience_score"] for item in scenarios[:3]) / max(1, min(3, len(scenarios))),
            2,
        )
        headline = (
            "Ownership is resilient against contributor loss."
            if scenarios and scenarios[0]["resilience_score"] >= 75
            else "Contributor concentration poses delivery risk under shock scenarios."
        )

        return {
            "headline": headline,
            "baseline_bus_factor_50_percent": baseline_bus_factor,
            "resilience_score": resilience_baseline,
            "single_point_of_failure": top_share >= 50,
            "top_contributor_share_percent": top_share,
            "contributors_considered": contributor_rows[:10],
            "scenarios": scenarios,
        }

    def _engineering_weather_forecast(
        self,
        weekly_digest: Dict[str, Any],
        risk_flags: List[Dict[str, Any]],
        release_readiness: Dict[str, Any],
        anomaly_report: Dict[str, Any],
        health_scorecard: Dict[str, Any],
    ) -> Dict[str, Any]:
        weeks = weekly_digest.get("weeks") or []
        if not weeks:
            return {
                "outlook": "unknown",
                "pressure_index": 0,
                "confidence": 0,
                "signals": [],
                "projected_weeks": [],
                "forecast_summary": "Forecast unavailable: not enough weekly activity data.",
            }

        recent_weeks = weeks[-8:]
        commit_series = [int(item.get("commits", 0) or 0) for item in recent_weeks]
        avg_commits = sum(commit_series) / max(1, len(commit_series))
        variance = sum((value - avg_commits) ** 2 for value in commit_series) / max(1, len(commit_series))
        volatility = math.sqrt(variance)
        volatility_percent = (volatility / avg_commits) * 100 if avg_commits > 0 else 0.0

        latest = (weekly_digest.get("latest") or recent_weeks[-1]) if recent_weeks else {}
        trend = weekly_digest.get("trend") or {}
        momentum = str(trend.get("momentum", "stable"))
        night_ratio = float(latest.get("night_commit_ratio", 0) or 0)
        high_risk_flags = sum(1 for flag in risk_flags if flag.get("severity") == "high")
        medium_risk_flags = sum(1 for flag in risk_flags if flag.get("severity") == "medium")
        readiness_score = float(
            release_readiness.get("score", health_scorecard.get("overall_score", 0)) or 0
        )
        anomaly_risk = float(anomaly_report.get("risk_index", 0) or 0)

        pressure_index = round(
            _clamp(
                high_risk_flags * 15
                + medium_risk_flags * 7
                + max(0.0, night_ratio - 12) * 0.8
                + volatility_percent * 0.4
                + max(0.0, 65 - readiness_score) * 0.55
                + anomaly_risk * 0.25,
                0.0,
                100.0,
            ),
            2,
        )

        if momentum == "improving" and pressure_index < 38:
            outlook = "sunny"
        elif pressure_index < 62:
            outlook = "cloudy"
        else:
            outlook = "stormy"

        base_commits = max(1, int(latest.get("commits", round(avg_commits)) or 1))
        slope = 1.04 if outlook == "sunny" else 0.99 if outlook == "cloudy" else 0.93
        spread = max(2, int(round(max(volatility, base_commits * 0.15))))

        projected_weeks = []
        for offset in range(1, 4):
            center = max(1, int(round(base_commits * (slope**offset))))
            projected_weeks.append(
                {
                    "week_offset": offset,
                    "label": f"+{offset}w",
                    "expected_min_commits": max(0, center - spread),
                    "expected_max_commits": center + spread,
                    "expected_mid_commits": center,
                    "risk_level": "high" if outlook == "stormy" else "medium" if outlook == "cloudy" else "low",
                }
            )

        incident_risk = round(_clamp(pressure_index * 0.85 + high_risk_flags * 6, 5.0, 95.0), 2)
        expected_review_lag_hours = round(
            max(4.0, 8 + pressure_index * 0.18 + max(0.0, night_ratio - 15) * 0.05),
            1,
        )
        confidence = round(_clamp(52 + len(recent_weeks) * 4 - volatility_percent * 0.35, 35.0, 95.0), 2)

        signals = [
            {"name": "Momentum", "value": momentum},
            {"name": "Volatility (%)", "value": round(volatility_percent, 2)},
            {"name": "Night Commit Ratio (%)", "value": round(night_ratio, 2)},
            {"name": "Anomaly Risk Index", "value": round(anomaly_risk, 2)},
            {"name": "Release Readiness", "value": round(readiness_score, 2)},
        ]

        summary = (
            "Stable trajectory with low operational pressure."
            if outlook == "sunny"
            else "Mixed signals; prioritize risk controls while maintaining velocity."
            if outlook == "cloudy"
            else "Elevated delivery pressure forecasted; reduce risk before scaling release pace."
        )

        return {
            "outlook": outlook,
            "pressure_index": pressure_index,
            "confidence": confidence,
            "incident_risk_percent": incident_risk,
            "expected_review_lag_hours": expected_review_lag_hours,
            "signals": signals,
            "projected_weeks": projected_weeks,
            "forecast_summary": summary,
        }

    def _pr_pre_mortem_simulator(
        self,
        blast_radius: Dict[str, Any],
        hotspots: List[Dict[str, Any]],
        top_contributors: List[Dict[str, Any]],
        engineering_signals: Dict[str, Any],
    ) -> Dict[str, Any]:
        candidates = (blast_radius.get("candidates") or [])[:8]
        if not candidates and hotspots:
            candidates = [
                {
                    "path": item.get("path"),
                    "directory": (str(item.get("path"))).rsplit("/", 1)[0] if "/" in str(item.get("path")) else ".",
                    "estimated_neighbor_files": 8,
                    "complexity": float(item.get("cyclomatic_complexity", 0) or 0),
                    "size_bytes": 0,
                    "impact_score": float(item.get("cyclomatic_complexity", 0) or 0) * 2.8,
                    "risk_tier": "high" if float(item.get("cyclomatic_complexity", 0) or 0) >= 18 else "medium",
                }
                for item in hotspots[:8]
            ]

        reviewers = [
            str(item.get("name") or item.get("email") or "unknown")
            for item in top_contributors[:6]
            if _safe_int(item.get("commits"), 0) > 0
        ]
        if not reviewers:
            reviewers = ["module owner", "tech lead"]

        scenarios = []
        for idx, candidate in enumerate(candidates):
            path = str(candidate.get("path", "unknown"))
            complexity = float(candidate.get("complexity", candidate.get("cyclomatic_complexity", 0)) or 0)
            impact_score = float(candidate.get("impact_score", 0) or 0)
            neighbor_files = int(candidate.get("estimated_neighbor_files", 1) or 1)
            size_bytes = int(candidate.get("size_bytes", 0) or 0)
            risk_score = round(
                _clamp(impact_score + complexity * 0.9 + math.log2(max(2, neighbor_files)) * 3, 0.0, 100.0),
                2,
            )

            failure_modes = []
            if complexity >= 20:
                failure_modes.append(
                    {
                        "mode": "branch_logic_regression",
                        "label": "Branch-heavy logic may regress on edge paths.",
                        "probability_percent": round(_clamp(42 + complexity * 1.1, 0.0, 95.0), 2),
                    }
                )
            if neighbor_files >= 40:
                failure_modes.append(
                    {
                        "mode": "integration_side_effect",
                        "label": "Wide module surface increases hidden integration side-effects.",
                        "probability_percent": round(_clamp(35 + neighbor_files * 0.6, 0.0, 95.0), 2),
                    }
                )
            if size_bytes >= 250000:
                failure_modes.append(
                    {
                        "mode": "review_blind_spot",
                        "label": "Large artifact size can reduce review depth and miss subtle defects.",
                        "probability_percent": round(_clamp(28 + math.log2(size_bytes + 1) * 4, 0.0, 90.0), 2),
                    }
                )
            if risk_score >= 70:
                failure_modes.append(
                    {
                        "mode": "rollback_likelihood",
                        "label": "High blast-radius score indicates elevated rollback risk.",
                        "probability_percent": round(_clamp(30 + risk_score * 0.5, 0.0, 95.0), 2),
                    }
                )
            if not failure_modes:
                failure_modes.append(
                    {
                        "mode": "localized_regression",
                        "label": "Localized functional regression remains possible.",
                        "probability_percent": round(_clamp(18 + risk_score * 0.25, 0.0, 70.0), 2),
                    }
                )

            mitigations = [
                "Add targeted regression tests for changed interfaces and edge paths.",
                "Assign at least one reviewer with recent ownership in this directory.",
                "Use a small-scope rollout plan with measurable rollback signals.",
            ]
            if risk_score >= 70:
                mitigations.append("Deploy behind feature flags or staged canary gates.")
            if not engineering_signals.get("has_ci"):
                mitigations.append("Run manual smoke tests until CI coverage is available.")

            suggested_reviewers = [
                reviewers[(idx + offset) % len(reviewers)]
                for offset in range(min(3, len(reviewers)))
            ]
            estimated_review_hours = int(round(max(2.0, risk_score / 18 + len(failure_modes))))

            scenarios.append(
                {
                    "scenario_id": f"pm-{idx + 1}",
                    "target_path": path,
                    "directory": candidate.get("directory", "."),
                    "risk_score": risk_score,
                    "risk_tier": candidate.get("risk_tier", "medium"),
                    "estimated_review_hours": estimated_review_hours,
                    "failure_modes": failure_modes,
                    "mitigations": mitigations[:5],
                    "suggested_reviewers": suggested_reviewers,
                }
            )

        portfolio_risk = round(
            sum(item["risk_score"] for item in scenarios) / max(1, len(scenarios)),
            2,
        )
        return {
            "portfolio_risk_score": portfolio_risk,
            "high_risk_targets": sum(1 for item in scenarios if item["risk_score"] >= 70),
            "scenarios": scenarios,
        }

    def _ai_action_briefs(
        self,
        pre_mortem: Dict[str, Any],
        bus_factor_shock: Dict[str, Any],
        engineering_forecast: Dict[str, Any],
        anomaly_report: Dict[str, Any],
        release_readiness: Dict[str, Any],
        risk_flags: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        briefs: List[Dict[str, Any]] = []

        def add_brief(
            priority: str,
            title: str,
            owner_role: str,
            why_now: str,
            first_steps: List[str],
            success_metric: str,
            timeline_days: int,
        ):
            briefs.append(
                {
                    "priority": priority,
                    "title": title,
                    "owner_role": owner_role,
                    "why_now": why_now,
                    "first_steps": first_steps[:4],
                    "success_metric": success_metric,
                    "timeline_days": timeline_days,
                }
            )

        top_scenario = (pre_mortem.get("scenarios") or [{}])[0]
        if top_scenario and top_scenario.get("target_path"):
            top_risk = float(top_scenario.get("risk_score", 0) or 0)
            add_brief(
                priority="P0" if top_risk >= 80 else "P1",
                title=f"Harden hotspot: {top_scenario.get('target_path')}",
                owner_role="Module owner + QA partner",
                why_now=f"Pre-mortem risk score is {round(top_risk, 2)} with elevated blast radius.",
                first_steps=[
                    "Add boundary tests and a rollback validation checklist for this path.",
                    "Break upcoming PRs into isolated slices limited to one risk mode.",
                    "Gate merge on two approvals including one reviewer outside the primary owner.",
                ],
                success_metric="Reduce hotspot risk score by >=15 points over the next two runs.",
                timeline_days=10,
            )

        shock_scenarios = bus_factor_shock.get("scenarios") or []
        weakest_shock = min(shock_scenarios, key=lambda x: float(x.get("resilience_score", 0))) if shock_scenarios else None
        if weakest_shock:
            resilience = float(weakest_shock.get("resilience_score", 0) or 0)
            removed = ", ".join((weakest_shock.get("removed_contributors") or [])[:2]) or "core owners"
            add_brief(
                priority="P0" if resilience < 45 else "P1",
                title="Reduce ownership concentration risk",
                owner_role="Engineering manager + tech leads",
                why_now=f"Shock test drops resilience to {round(resilience, 2)} when {removed} are unavailable.",
                first_steps=[
                    "Create a two-week ownership rotation for top two critical directories.",
                    "Require shadow reviewers from a second team on high-risk PRs.",
                    "Document runbooks for the top three blast-radius modules.",
                ],
                success_metric="Increase shock-test resilience score to >=65 in the next analysis cycle.",
                timeline_days=14,
            )

        anomaly_risk = float(anomaly_report.get("risk_index", 0) or 0)
        if anomaly_risk >= 35:
            add_brief(
                priority="P1",
                title="Normalize anomalous delivery patterns",
                owner_role="Release captain",
                why_now=f"Anomaly risk index is {round(anomaly_risk, 2)} with unusual commit patterns.",
                first_steps=[
                    "Flag mega-commit and wide-surface changes for synchronous review before merge.",
                    "Add PR template checks for off-hours high-change submissions.",
                    "Run weekly anomaly review in sprint quality sync.",
                ],
                success_metric="Cut anomaly rate by 30% while maintaining weekly throughput.",
                timeline_days=7,
            )

        outlook = str(engineering_forecast.get("outlook", "unknown"))
        forecast_pressure = float(engineering_forecast.get("pressure_index", 0) or 0)
        if outlook in {"cloudy", "stormy"}:
            add_brief(
                priority="P1" if outlook == "cloudy" else "P0",
                title="Stabilize delivery weather",
                owner_role="Tech lead",
                why_now=f"Forecast outlook is {outlook.upper()} with pressure index {round(forecast_pressure, 2)}.",
                first_steps=[
                    "Limit concurrent high-risk changes per sprint lane.",
                    "Allocate explicit time for debt and test reinforcement in next iteration.",
                    "Track review lag and incident risk as release guardrails.",
                ],
                success_metric="Move forecast outlook to SUNNY/CLOUDY with pressure index <45.",
                timeline_days=10,
            )

        high_risk_flags = [flag.get("message", "") for flag in risk_flags if flag.get("severity") == "high"]
        readiness_score = float(release_readiness.get("score", 0) or 0)
        if readiness_score < 80 or high_risk_flags:
            add_brief(
                priority="P1" if readiness_score >= 65 else "P0",
                title="Raise release confidence",
                owner_role="Release manager",
                why_now=f"Release readiness score is {round(readiness_score, 2)} and needs hardening.",
                first_steps=[
                    "Close failing release gates and unresolved high-severity risk flags.",
                    "Add a pre-release dry run with rollback rehearsal.",
                    "Publish a release checklist owned by cross-functional reviewers.",
                ],
                success_metric="Improve readiness score to >=85 with zero failing gates.",
                timeline_days=14,
            )

        if not briefs:
            add_brief(
                priority="P2",
                title="Keep healthy engineering cadence",
                owner_role="Team leads",
                why_now="Current indicators are stable; preserve reliability as velocity scales.",
                first_steps=[
                    "Continue weekly quality and ownership reviews.",
                    "Monitor hotspot score drift and forecast pressure.",
                    "Capture learnings from major PRs in lightweight runbooks.",
                ],
                success_metric="Maintain health and readiness scores above 80.",
                timeline_days=14,
            )

        priority_rank = {"P0": 0, "P1": 1, "P2": 2}
        briefs = sorted(briefs, key=lambda item: priority_rank.get(item["priority"], 99))[:6]
        top_priority = briefs[0] if briefs else None
        roadmap = [
            {
                "window": "Days 1-3",
                "focus": briefs[0]["title"] if len(briefs) > 0 else "Stabilize top risk",
            },
            {
                "window": "Days 4-7",
                "focus": briefs[1]["title"] if len(briefs) > 1 else "Improve ownership resilience",
            },
            {
                "window": "Week 2",
                "focus": briefs[2]["title"] if len(briefs) > 2 else "Lift readiness score",
            },
        ]
        narrative = (
            f"Top action: {top_priority['title']} ({top_priority['priority']})"
            if top_priority
            else "No action briefs available."
        )

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "top_priority": top_priority,
            "briefs": briefs,
            "roadmap": roadmap,
            "narrative": narrative,
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
        shock_test = insights.get("bus_factor_shock_test", {})
        forecast = insights.get("engineering_weather_forecast", {})
        anomalies = insights.get("anomaly_detective", {})
        action_briefs = insights.get("ai_action_briefs", {})

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
        if shock_test:
            lines.append(
                f"Bus-factor shock resilience is {shock_test.get('resilience_score', 0)} with top-share concentration at {shock_test.get('top_contributor_share_percent', 0)}%."
            )
        if forecast:
            lines.append(
                f"Engineering weather outlook is {str(forecast.get('outlook', 'unknown')).upper()} (pressure index {forecast.get('pressure_index', 0)})."
            )
        if anomalies:
            lines.append(
                f"Anomaly detective flagged {anomalies.get('anomaly_count', 0)} events (risk index {anomalies.get('risk_index', 0)})."
            )
        if action_briefs and action_briefs.get("top_priority"):
            lines.append(
                f"Top recommended action: {action_briefs.get('top_priority', {}).get('title', 'N/A')}."
            )
        if complexity["hotspots"]:
            top = complexity["hotspots"][0]
            lines.append(
                f"Top hotspot: {top.get('path')} (complexity={top.get('cyclomatic_complexity')})."
            )
        return lines
