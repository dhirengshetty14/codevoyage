"use client"

import { useEffect, useMemo, useState } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { api } from "@/lib/api"
import { useAnalysisStream } from "@/hooks/useAnalysisStream"

type Analysis = {
  id: string
  status: string
  progress: number
  error_message?: string | null
  ai_insights?: any
  language_evolution?: Record<string, number>
  contributor_network?: any[]
  commits_analyzed?: number
  processing_time_seconds?: number
}

const STAGE_ORDER = [
  "starting",
  "analyzing_git_data",
  "cloning_repository",
  "git_clone_complete",
  "commit_extraction_complete",
  "contributor_extraction_complete",
  "file_tree_extraction_complete",
  "git_analysis_complete",
  "analyzing_complexity",
  "complexity_scan_complete",
  "complexity_analysis_complete",
  "generating_ai_insights",
  "ai_insights_skipped",
  "ai_insights_generated",
  "compiling_results",
  "completed",
]

const COLORS = ["#38bdf8", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#f97316", "#14b8a6"]

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState("")
  const [repoName, setRepoName] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [activeRepoId, setActiveRepoId] = useState<string | null>(null)
  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [snapshotDiff, setSnapshotDiff] = useState<any | null>(null)
  const [selectedBlastPath, setSelectedBlastPath] = useState<string>("")
  const [timelineIndex, setTimelineIndex] = useState<number>(0)
  const [selectedPreMortemId, setSelectedPreMortemId] = useState<string>("")
  const [shockScenarioIndex, setShockScenarioIndex] = useState<number>(0)

  const stream = useAnalysisStream(activeAnalysisId ?? undefined)
  const deterministic = analysis?.ai_insights?.deterministic_insights

  useEffect(() => {
    if (!stream.progress) return
    const progressEvent = stream.progress
    setAnalysis((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        progress: progressEvent.progress,
        status: progressEvent.status,
        error_message: progressEvent.error_message,
      }
    })
  }, [stream.progress])

  useEffect(() => {
    if (!activeAnalysisId) return
    if (analysis?.status === "completed" || analysis?.status === "failed") return

    const timer = setInterval(async () => {
      try {
        const latest = await api.getAnalysis(activeAnalysisId)
        setAnalysis(latest)
      } catch {
        // best effort polling
      }
    }, 2500)

    return () => clearInterval(timer)
  }, [activeAnalysisId, analysis?.status])

  useEffect(() => {
    if (!activeRepoId || analysis?.status !== "completed") return
    api.getRepositorySnapshotDiff(activeRepoId)
      .then(setSnapshotDiff)
      .catch(() => setSnapshotDiff(null))
  }, [activeRepoId, analysis?.status])

  const handleAnalyze = async () => {
    if (!repoUrl.trim() || isSubmitting) return
    setIsSubmitting(true)
    try {
      const inferredName = repoUrl.trim().split("/").filter(Boolean).pop()?.replace(".git", "") || "repository"
      const repository = await api.createRepository({
        name: repoName.trim() || inferredName,
        url: repoUrl.trim(),
      })
      setActiveRepoId(repository.id)

      const created = await api.createAnalysis(repository.id)
      setActiveAnalysisId(created.id)
      setAnalysis(created)
    } finally {
      setIsSubmitting(false)
    }
  }

  const stageProgress = useMemo(() => {
    const status = analysis?.status || "starting"
    return Math.max(0, STAGE_ORDER.indexOf(status))
  }, [analysis?.status])

  const languageData = deterministic?.language_profile?.languages || []
  const hourData = deterministic?.development_habits?.most_active_hours || []
  const contributorData = deterministic?.team_dynamics?.top_contributors || []
  const sizeDistribution = deterministic?.repository_structure?.size_distribution || []
  const riskFlags = deterministic?.risk_flags || []
  const largestFiles = deterministic?.repository_structure?.largest_files || []
  const healthDimensions = Object.entries(deterministic?.health_scorecard?.dimensions || {}).map(([key, value]) => ({
    dimension: key.replaceAll("_", " "),
    score: Number(value || 0),
  }))
  const blastCandidates = deterministic?.blast_radius?.candidates || []
  const selectedBlast = blastCandidates.find((x: any) => x.path === selectedBlastPath) || blastCandidates[0]
  const timePoints = deterministic?.time_machine?.points || []
  const clampedTimelineIndex = Math.min(Math.max(0, timelineIndex), Math.max(0, timePoints.length - 1))
  const timelinePoint = timePoints[clampedTimelineIndex] || null
  const timeMachineSeries = useMemo(
    () =>
      timePoints.map((point: any, idx: number) => ({
        ...point,
        cumulative_visible: idx <= clampedTimelineIndex ? point.cumulative_commits : null,
      })),
    [timePoints, clampedTimelineIndex]
  )
  const fingerprint = deterministic?.repo_fingerprint
  const preMortemScenarios = deterministic?.pr_pre_mortem?.scenarios || []
  const selectedPreMortem =
    preMortemScenarios.find((scenario: any) => scenario.scenario_id === selectedPreMortemId) || preMortemScenarios[0]
  const shockScenarios = deterministic?.bus_factor_shock_test?.scenarios || []
  const clampedShockScenarioIndex = Math.min(Math.max(0, shockScenarioIndex), Math.max(0, shockScenarios.length - 1))
  const selectedShockScenario = shockScenarios[clampedShockScenarioIndex] || null
  const forecast = deterministic?.engineering_weather_forecast
  const forecastSeries = forecast?.projected_weeks || []
  const anomalyDetective = deterministic?.anomaly_detective
  const anomalyCounts = anomalyDetective?.counts_by_type || []
  const anomalyHighlights = anomalyDetective?.highlights || []
  const actionBriefs = deterministic?.ai_action_briefs?.briefs || []
  const topBrief = deterministic?.ai_action_briefs?.top_priority
  const shockSeries = shockScenarios.map((scenario: any) => ({
    removed: scenario.removed_count,
    resilience: scenario.resilience_score,
    coverageLost: scenario.coverage_lost_percent,
  }))
  const forecastTone =
    forecast?.outlook === "sunny"
      ? "border-emerald-400/40 bg-emerald-500/10 text-emerald-300"
      : forecast?.outlook === "cloudy"
        ? "border-amber-400/40 bg-amber-500/10 text-amber-300"
        : "border-rose-400/40 bg-rose-500/10 text-rose-300"

  useEffect(() => {
    if (!timePoints.length) return
    setTimelineIndex((prev) => Math.min(prev, timePoints.length - 1))
  }, [timePoints.length])

  useEffect(() => {
    if (!preMortemScenarios.length) {
      setSelectedPreMortemId("")
      return
    }
    setSelectedPreMortemId((prev) => {
      if (prev && preMortemScenarios.some((scenario: any) => scenario.scenario_id === prev)) return prev
      return preMortemScenarios[0].scenario_id
    })
  }, [preMortemScenarios.length, deterministic?.pr_pre_mortem?.portfolio_risk_score])

  useEffect(() => {
    if (!shockScenarios.length) {
      setShockScenarioIndex(0)
      return
    }
    setShockScenarioIndex((prev) => Math.min(prev, shockScenarios.length - 1))
  }, [shockScenarios.length, deterministic?.bus_factor_shock_test?.resilience_score])

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
          <h1 className="text-4xl font-bold tracking-tight">CodeVoyage</h1>
          <p className="mt-2 text-slate-300">
            Codebase analytics with meaningful insights and visual signals.
          </p>
        </header>

        <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-xl font-semibold">Start Analysis</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <input
              className="rounded-lg border border-white/20 bg-black/30 px-3 py-2"
              placeholder="https://github.com/org/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
            />
            <input
              className="rounded-lg border border-white/20 bg-black/30 px-3 py-2"
              placeholder="Display name (optional)"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
            />
            <button
              className="rounded-lg bg-cyan-500 px-3 py-2 font-semibold text-slate-950 disabled:opacity-50"
              onClick={handleAnalyze}
              disabled={!repoUrl.trim() || isSubmitting}
            >
              {isSubmitting ? "Submitting..." : "Analyze Repository"}
            </button>
          </div>
          {activeRepoId && <p className="mt-2 text-sm text-slate-300">Repository ID: {activeRepoId}</p>}
        </section>

        <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Live Status</h2>
            {analysis?.status && (
              <span className="rounded-full border border-white/20 px-3 py-1 text-sm uppercase tracking-wide">
                {analysis.status}
              </span>
            )}
          </div>

          {!analysis && <p className="mt-3 text-slate-300">No active analysis.</p>}

          {analysis && (
            <>
              <div className="mt-3 text-sm text-slate-300">
                <p>Analysis ID: {analysis.id}</p>
                <p>Progress: {analysis.progress}%</p>
                {analysis.error_message && <p className="text-red-400">Error: {analysis.error_message}</p>}
              </div>

              <div className="mt-4 h-3 w-full rounded bg-slate-800">
                <div
                  className="h-3 rounded bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all"
                  style={{ width: `${analysis.progress}%` }}
                />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2 text-xs md:grid-cols-4 xl:grid-cols-8">
                {STAGE_ORDER.slice(0, 16).map((stage, idx) => {
                  const active = idx <= stageProgress
                  return (
                    <div
                      key={stage}
                      className={`rounded border px-2 py-1 ${
                        active ? "border-cyan-400 bg-cyan-400/20 text-cyan-200" : "border-white/10 bg-black/20 text-slate-400"
                      }`}
                    >
                      {stage}
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </section>

        {analysis?.status === "completed" && (
          <>
            <section className="mt-6 grid gap-4 md:grid-cols-5">
              <StatCard title="Commits" value={String(deterministic?.summary?.total_commits_analyzed ?? analysis.commits_analyzed ?? 0)} />
              <StatCard title="Contributors" value={String(deterministic?.summary?.total_contributors ?? analysis.contributor_network?.length ?? 0)} />
              <StatCard title="Code Changes" value={String(deterministic?.summary?.total_code_changes ?? 0)} />
              <StatCard title="Files" value={String(deterministic?.repository_structure?.total_files ?? 0)} />
              <StatCard title="Confidence" value={`${deterministic?.insight_quality?.confidence_score ?? 0}/100`} />
            </section>

            <section className="mt-6 grid gap-4 lg:grid-cols-2">
              <Panel title="Repo DNA Fingerprint">
                <p className="text-lg font-semibold text-cyan-300">{fingerprint?.tagline || "No fingerprint yet"}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(fingerprint?.labels || []).map((label: string, idx: number) => (
                    <span key={idx} className="rounded-full border border-cyan-300/30 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-200">
                      {label}
                    </span>
                  ))}
                </div>
              </Panel>

              <Panel title="Engineering Health Scorecard">
                <div className="mb-3 text-sm text-slate-300">
                  Overall Score: <span className="text-2xl font-bold text-emerald-300">{deterministic?.health_scorecard?.overall_score ?? 0}</span>
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={healthDimensions}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="dimension" stroke="#cbd5e1" interval={0} angle={-15} textAnchor="end" height={70} />
                    <YAxis stroke="#cbd5e1" domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="score" fill="#22c55e" />
                  </BarChart>
                </ResponsiveContainer>
              </Panel>
            </section>

            <section className="mt-6 grid gap-4 lg:grid-cols-2">
              <ChartCard title="Language Distribution">
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={languageData} dataKey="files" nameKey="language" outerRadius={100} label>
                      {languageData.map((_: any, idx: number) => (
                        <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Most Active Commit Hours">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={hourData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="hour" stroke="#cbd5e1" />
                    <YAxis stroke="#cbd5e1" />
                    <Tooltip />
                    <Bar dataKey="commits" fill="#22d3ee" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Repository File Size Distribution">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={sizeDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="bucket" stroke="#cbd5e1" />
                    <YAxis stroke="#cbd5e1" />
                    <Tooltip />
                    <Bar dataKey="files" fill="#a78bfa" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Contributor Ownership (Top)">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={contributorData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#cbd5e1" interval={0} angle={-15} textAnchor="end" height={60} />
                    <YAxis stroke="#cbd5e1" />
                    <Tooltip />
                    <Bar dataKey="commits" fill="#34d399" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </section>

            <section className="mt-6 grid gap-4 lg:grid-cols-2">
              <Panel title="Codebase Time Machine">
                <div className="text-sm text-slate-300">
                  {timelinePoint ? (
                    <>
                      <p>Date: {timelinePoint.date}</p>
                      <p>Commit: {timelinePoint.commit_sha}</p>
                      <p>Author: {timelinePoint.author}</p>
                      <p>Cumulative Commits: {timelinePoint.cumulative_commits}</p>
                    </>
                  ) : (
                    <p>No timeline data available.</p>
                  )}
                </div>
                <div className="mt-3">
                  <input
                    type="range"
                    min={0}
                    max={Math.max(0, timePoints.length - 1)}
                    value={Math.min(timelineIndex, Math.max(0, timePoints.length - 1))}
                    onChange={(e) => setTimelineIndex(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={timeMachineSeries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#cbd5e1" hide={timePoints.length > 80} />
                    <YAxis stroke="#cbd5e1" />
                    <Tooltip />
                    <Line type="monotone" dataKey="cumulative_commits" stroke="#1e293b" dot={false} strokeWidth={2} />
                    <Line type="monotone" dataKey="cumulative_visible" stroke="#22d3ee" dot={false} strokeWidth={3} />
                    {timelinePoint && (
                      <ReferenceDot
                        x={timelinePoint.date}
                        y={timelinePoint.cumulative_commits}
                        r={5}
                        fill="#38bdf8"
                        stroke="#ffffff"
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </Panel>

              <Panel title="Blast Radius Simulator">
                <div className="mb-3">
                  <select
                    className="w-full rounded border border-white/20 bg-black/30 px-3 py-2"
                    value={selectedBlastPath || selectedBlast?.path || ""}
                    onChange={(e) => setSelectedBlastPath(e.target.value)}
                  >
                    {blastCandidates.map((c: any, idx: number) => (
                      <option key={idx} value={c.path}>{c.path}</option>
                    ))}
                  </select>
                </div>
                {selectedBlast ? (
                  <div className="space-y-1 text-sm text-slate-300">
                    <p>Impact Score: <span className="font-semibold text-cyan-300">{selectedBlast.impact_score}</span></p>
                    <p>Risk Tier: <span className="font-semibold uppercase">{selectedBlast.risk_tier}</span></p>
                    <p>Directory: {selectedBlast.directory}</p>
                    <p>Estimated Neighbor Files Affected: {selectedBlast.estimated_neighbor_files}</p>
                    <p>Complexity: {selectedBlast.complexity}</p>
                  </div>
                ) : (
                  <p className="text-slate-400">No candidates available.</p>
                )}
              </Panel>
            </section>

            <section className="mt-6 grid gap-4 lg:grid-cols-2">
              <Panel title="PR Pre-Mortem Simulator">
                <div className="text-sm text-slate-300">
                  <p>
                    Portfolio Risk Score:{" "}
                    <span className="font-semibold text-cyan-300">
                      {deterministic?.pr_pre_mortem?.portfolio_risk_score ?? 0}
                    </span>
                  </p>
                  <p>High-Risk Targets: {deterministic?.pr_pre_mortem?.high_risk_targets ?? 0}</p>
                </div>
                {preMortemScenarios.length > 0 ? (
                  <>
                    <div className="mt-3">
                      <select
                        className="w-full rounded border border-white/20 bg-black/30 px-3 py-2"
                        value={selectedPreMortemId || selectedPreMortem?.scenario_id || ""}
                        onChange={(e) => setSelectedPreMortemId(e.target.value)}
                      >
                        {preMortemScenarios.map((scenario: any, idx: number) => (
                          <option key={idx} value={scenario.scenario_id}>
                            {scenario.target_path}
                          </option>
                        ))}
                      </select>
                    </div>

                    {selectedPreMortem && (
                      <div className="mt-4 space-y-2 text-sm text-slate-300">
                        <p>
                          Risk Score: <span className="font-semibold text-cyan-300">{selectedPreMortem.risk_score}</span>
                        </p>
                        <p>Risk Tier: <span className="font-semibold uppercase">{selectedPreMortem.risk_tier}</span></p>
                        <p>Estimated Review Hours: {selectedPreMortem.estimated_review_hours}</p>
                        <p>Directory: {selectedPreMortem.directory}</p>
                        <div>
                          <p className="font-semibold text-slate-200">Failure Modes</p>
                          <ul className="mt-1 list-disc space-y-1 pl-5">
                            {(selectedPreMortem.failure_modes || []).slice(0, 3).map((mode: any, idx: number) => (
                              <li key={idx}>
                                {mode.label} ({mode.probability_percent}%)
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-semibold text-slate-200">Mitigations</p>
                          <ul className="mt-1 list-disc space-y-1 pl-5">
                            {(selectedPreMortem.mitigations || []).slice(0, 3).map((step: string, idx: number) => (
                              <li key={idx}>{step}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="mt-3 text-slate-400">No pre-mortem scenarios available.</p>
                )}
              </Panel>

              <Panel title="Bus-Factor Shock Test">
                <div className="text-sm text-slate-300">
                  <p>
                    Baseline Bus Factor(50%):{" "}
                    <span className="font-semibold text-cyan-300">
                      {deterministic?.bus_factor_shock_test?.baseline_bus_factor_50_percent ?? 0}
                    </span>
                  </p>
                  <p>Resilience Score: {deterministic?.bus_factor_shock_test?.resilience_score ?? 0}</p>
                </div>

                {shockScenarios.length > 0 ? (
                  <>
                    <div className="mt-3">
                      <input
                        type="range"
                        min={0}
                        max={Math.max(0, shockScenarios.length - 1)}
                        value={clampedShockScenarioIndex}
                        onChange={(e) => setShockScenarioIndex(Number(e.target.value))}
                        className="w-full"
                      />
                      <p className="mt-1 text-xs text-slate-400">
                        Simulating loss of top {selectedShockScenario?.removed_count ?? 0} contributor(s)
                      </p>
                    </div>

                    {selectedShockScenario && (
                      <div className="mt-3 space-y-1 text-sm text-slate-300">
                        <p>Coverage Lost: {selectedShockScenario.coverage_lost_percent}%</p>
                        <p>New Bus Factor(50%): {selectedShockScenario.new_bus_factor_50_percent}</p>
                        <p>
                          Risk Tier:{" "}
                          <span className="font-semibold uppercase">{selectedShockScenario.risk_tier}</span>
                        </p>
                        <p>Recovery Estimate: {selectedShockScenario.recovery_days_estimate} days</p>
                      </div>
                    )}

                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={shockSeries}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="removed" stroke="#cbd5e1" />
                        <YAxis stroke="#cbd5e1" domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="resilience" fill="#38bdf8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </>
                ) : (
                  <p className="mt-3 text-slate-400">No shock-test scenarios available.</p>
                )}
              </Panel>
            </section>

            <section className="mt-6 grid gap-4 lg:grid-cols-2">
              <Panel title="Engineering Weather Forecast">
                {forecast ? (
                  <>
                    <div className="mb-3 flex items-center justify-between">
                      <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase ${forecastTone}`}>
                        {forecast.outlook}
                      </span>
                      <span className="text-sm text-slate-300">
                        Confidence: <span className="font-semibold">{forecast.confidence}</span>
                      </span>
                    </div>
                    <div className="space-y-1 text-sm text-slate-300">
                      <p>Pressure Index: {forecast.pressure_index}</p>
                      <p>Incident Risk: {forecast.incident_risk_percent}%</p>
                      <p>Expected Review Lag: {forecast.expected_review_lag_hours}h</p>
                      <p className="text-slate-200">{forecast.forecast_summary}</p>
                    </div>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={forecastSeries}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="label" stroke="#cbd5e1" />
                        <YAxis stroke="#cbd5e1" />
                        <Tooltip />
                        <Line type="monotone" dataKey="expected_mid_commits" stroke="#22d3ee" strokeWidth={3} />
                        <Line type="monotone" dataKey="expected_max_commits" stroke="#f59e0b" strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  </>
                ) : (
                  <p className="text-slate-400">No forecast data available.</p>
                )}
              </Panel>

              <Panel title="Anomaly Detective">
                {anomalyDetective ? (
                  <>
                    <div className="space-y-1 text-sm text-slate-300">
                      <p>
                        Risk Index:{" "}
                        <span className="font-semibold text-cyan-300">{anomalyDetective.risk_index ?? 0}</span>
                      </p>
                      <p>Anomaly Count: {anomalyDetective.anomaly_count ?? 0}</p>
                      <p>Anomaly Rate: {anomalyDetective.anomaly_rate_percent ?? 0}%</p>
                    </div>
                    <ResponsiveContainer width="100%" height={210}>
                      <BarChart data={anomalyCounts}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="label" stroke="#cbd5e1" />
                        <YAxis stroke="#cbd5e1" />
                        <Tooltip />
                        <Bar dataKey="count" fill="#f97316" />
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="mt-2 space-y-1 text-xs text-slate-300">
                      {anomalyHighlights.slice(0, 3).map((item: any, idx: number) => (
                        <p key={idx}>
                          [{String(item.severity || "low").toUpperCase()}] {item.headline}
                        </p>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-slate-400">No anomaly report available.</p>
                )}
              </Panel>
            </section>

            <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
              <h3 className="text-lg font-semibold">AI Action Briefs</h3>
              {topBrief && (
                <p className="mt-2 text-sm text-cyan-200">
                  Top Priority ({topBrief.priority}): {topBrief.title}
                </p>
              )}
              {!actionBriefs.length && <p className="mt-2 text-slate-400">No action briefs available.</p>}
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {actionBriefs.map((brief: any, idx: number) => (
                  <div key={idx} className="rounded-lg border border-white/10 bg-black/20 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold text-slate-100">{brief.title}</p>
                      <span className="rounded-full border border-white/20 px-2 py-0.5 text-xs">{brief.priority}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-300">{brief.why_now}</p>
                    <p className="mt-2 text-xs text-slate-400">Owner: {brief.owner_role}</p>
                    <p className="mt-1 text-xs text-slate-400">ETA: {brief.timeline_days} days</p>
                    <p className="mt-2 text-xs text-emerald-300">Success: {brief.success_metric}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
              <h3 className="text-lg font-semibold">Snapshot Diff (Last Two Runs)</h3>
              {!snapshotDiff && <p className="mt-2 text-slate-300">Run this repository at least twice to get trend diff.</p>}
              {snapshotDiff && (
                <div className="mt-3 grid gap-4 md:grid-cols-2">
                  <div className="rounded border border-white/10 bg-black/20 p-4 text-sm">
                    <p>Health Score Delta: {snapshotDiff.summary_diff?.health_score_delta}</p>
                    <p>High Risk Files Delta: {snapshotDiff.summary_diff?.high_risk_files_delta}</p>
                    <p>Commits Analyzed Delta: {snapshotDiff.summary_diff?.commits_analyzed_delta}</p>
                    <p>Processing Time Delta (s): {snapshotDiff.summary_diff?.processing_time_delta_seconds}</p>
                  </div>
                  <div className="rounded border border-white/10 bg-black/20 p-4 text-sm">
                    <p>Ownership Delta: {snapshotDiff.scorecard_diff?.ownership_resilience_delta}</p>
                    <p>Reliability Delta: {snapshotDiff.scorecard_diff?.delivery_reliability_delta}</p>
                    <p>Complexity Health Delta: {snapshotDiff.scorecard_diff?.complexity_health_delta}</p>
                    <p>Fingerprint: {snapshotDiff.fingerprint?.target || "N/A"}</p>
                  </div>
                </div>
              )}
            </section>

            <section className="mt-6 grid gap-4 lg:grid-cols-2">
              <Panel title="Executive Summary">
                <ul className="list-disc space-y-2 pl-5 text-slate-200">
                  {(deterministic?.executive_summary || []).map((line: string, idx: number) => (
                    <li key={idx}>{line}</li>
                  ))}
                </ul>
              </Panel>

              <Panel title="Risk Flags">
                <div className="flex flex-wrap gap-2">
                  {riskFlags.length === 0 && <span className="text-slate-300">No major risks flagged.</span>}
                  {riskFlags.map((flag: any, idx: number) => (
                    <span
                      key={idx}
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        flag.severity === "high"
                          ? "bg-red-500/20 text-red-300"
                          : flag.severity === "medium"
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-cyan-500/20 text-cyan-300"
                      }`}
                    >
                      {flag.severity.toUpperCase()}: {flag.message}
                    </span>
                  ))}
                </div>

                <div className="mt-4 text-sm text-slate-300">
                  <p>Tests detected: {String(deterministic?.engineering_signals?.has_tests ?? false)}</p>
                  <p>CI detected: {String(deterministic?.engineering_signals?.has_ci ?? false)}</p>
                  <p>Docker detected: {String(deterministic?.engineering_signals?.has_docker ?? false)}</p>
                  <p>Notebooks: {deterministic?.engineering_signals?.notebook_count ?? 0}</p>
                </div>
              </Panel>
            </section>

            <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6">
              <h3 className="text-lg font-semibold">Largest Files</h3>
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-300">
                      <th className="py-2">Path</th>
                      <th className="py-2">Size (KB)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {largestFiles.slice(0, 12).map((f: any, idx: number) => (
                      <tr key={idx} className="border-t border-white/10">
                        <td className="py-2 text-slate-200">{f.path}</td>
                        <td className="py-2 text-slate-300">{(Number(f.size_bytes || 0) / 1024).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  )
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-sm text-slate-300">{title}</div>
      <div className="mt-1 text-2xl font-bold">{value}</div>
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-3">{children}</div>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-3">{children}</div>
    </div>
  )
}
