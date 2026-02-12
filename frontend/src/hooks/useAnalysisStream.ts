'use client'

import { useEffect, useState } from 'react'
import type { AnalysisProgress } from '@/types/domain'
import { useWebSocket } from '@/lib/websocket'

export function useAnalysisStream(analysisId?: string) {
  const { socket, subscribeToAnalysis, unsubscribeFromAnalysis } = useWebSocket()
  const [progress, setProgress] = useState<AnalysisProgress | null>(null)

  useEffect(() => {
    if (!analysisId) return
    subscribeToAnalysis(analysisId)

    return () => {
      unsubscribeFromAnalysis(analysisId)
    }
  }, [analysisId, subscribeToAnalysis, unsubscribeFromAnalysis])

  useEffect(() => {
    if (!socket || !analysisId) return

    const onProgress = (event: AnalysisProgress) => {
      if (event.analysis_id === analysisId) {
        setProgress(event)
      }
    }

    socket.on("analysis_progress", onProgress)
    return () => {
      socket.off("analysis_progress", onProgress)
    }
  }, [analysisId, socket])

  return {
    progress,
  }
}
