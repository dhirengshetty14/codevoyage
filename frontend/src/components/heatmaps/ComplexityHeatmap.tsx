'use client'

interface ComplexityHeatmapProps {
  hotspots: Array<{ path: string; score: number }>
}

export function ComplexityHeatmap({ hotspots }: ComplexityHeatmapProps) {
  return (
    <div className="rounded-xl border border-white/10 p-4 text-gray-300">
      <h3 className="mb-2 text-lg font-semibold text-white">Complexity Heatmap</h3>
      <p className="text-sm text-gray-400">3D overlay placeholder. Hotspots detected: {hotspots.length}</p>
    </div>
  )
}
