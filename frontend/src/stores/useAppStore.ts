import { create } from 'zustand'

type ViewMode = '3d' | 'timeline' | 'network'

interface AppStore {
  viewMode: ViewMode
  setViewMode: (mode: ViewMode) => void
}

export const useAppStore = create<AppStore>((set) => ({
  viewMode: '3d',
  setViewMode: (viewMode) => set({ viewMode }),
}))
