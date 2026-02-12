'use client'

interface LanguageSeriesPoint {
  timestamp: string
  [language: string]: string | number
}

interface LanguageTimelineProps {
  data: LanguageSeriesPoint[]
}

export function LanguageTimeline({ data }: LanguageTimelineProps) {
  return (
    <div className="rounded-xl border border-white/10 p-4 text-gray-300">
      <h3 className="mb-2 text-lg font-semibold text-white">Language Evolution Timeline</h3>
      <p className="text-sm text-gray-400">Stacked area timeline placeholder. Points loaded: {data.length}</p>
    </div>
  )
}
