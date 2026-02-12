export type AnalysisStatus = 'pending' | 'starting' | 'processing' | 'completed' | 'failed'

export interface AnalysisProgress {
  analysis_id: string
  progress: number
  status: AnalysisStatus | string
  error_message?: string | null
}
