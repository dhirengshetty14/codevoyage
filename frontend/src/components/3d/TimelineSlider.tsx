    "use client"

import React, { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Pause, SkipBack, SkipForward, GitCommit, Calendar, Users, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils'

interface Commit {
  id: string
  sha: string
  message: string
  author: string
  date: string
  files_changed: number
  insertions: number
  deletions: number
}

interface TimelineSliderProps {
  commits: Commit[]
  currentIndex: number
  onIndexChange: (index: number) => void
  onPlay?: () => void
  onPause?: () => void
  isPlaying?: boolean
  speed?: 'slow' | 'normal' | 'fast'
  onSpeedChange?: (speed: 'slow' | 'normal' | 'fast') => void
  className?: string
}

export function TimelineSlider({
  commits,
  currentIndex,
  onIndexChange,
  onPlay,
  onPause,
  isPlaying = false,
  speed = 'normal',
  onSpeedChange,
  className
}: TimelineSliderProps) {
  const [scrubbing, setScrubbing] = useState(false)
  const [showCommitInfo, setShowCommitInfo] = useState(false)
  const [currentCommit, setCurrentCommit] = useState<Commit | null>(null)

  const speedValues = {
    slow: 1500,
    normal: 800,
    fast: 300
  }

  const handleSliderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const index = parseInt(e.target.value)
    onIndexChange(index)
  }, [onIndexChange])

  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      onPause?.()
    } else {
      onPlay?.()
    }
  }, [isPlaying, onPlay, onPause])

  const handleSkipBack = useCallback(() => {
    const newIndex = Math.max(0, currentIndex - 1)
    onIndexChange(newIndex)
  }, [currentIndex, onIndexChange])

  const handleSkipForward = useCallback(() => {
    const newIndex = Math.min(commits.length - 1, currentIndex + 1)
    onIndexChange(newIndex)
  }, [currentIndex, commits.length, onIndexChange])

  const handleCommitClick = useCallback((commit: Commit, index: number) => {
    onIndexChange(index)
    setCurrentCommit(commit)
    setShowCommitInfo(true)
  }, [onIndexChange])

  useEffect(() => {
    if (commits.length > 0 && currentIndex < commits.length) {
      setCurrentCommit(commits[currentIndex])
    }
  }, [commits, currentIndex])

  const getCommitColor = (index: number) => {
    const commit = commits[index]
    const changes = (commit?.insertions || 0) + (commit?.deletions || 0)
    
    if (changes > 100) return 'bg-red-500'
    if (changes > 50) return 'bg-orange-500'
    if (changes > 10) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getTimelinePosition = (date: string) => {
    if (commits.length < 2) return 0
    
    const startDate = new Date(commits[0].date).getTime()
    const endDate = new Date(commits[commits.length - 1].date).getTime()
    const currentDate = new Date(date).getTime()
    
    return ((currentDate - startDate) / (endDate - startDate)) * 100
  }

  return (
    <div className={cn("relative w-full", className)}>
      {/* Main timeline track */}
      <div className="relative h-24 bg-gradient-to-r from-gray-900 via-purple-900 to-violet-800 rounded-xl p-4">
        {/* Timeline rail */}
        <div className="absolute top-1/2 left-0 right-0 h-1 bg-gray-700/50 transform -translate-y-1/2 rounded-full">
          {/* Progress indicator */}
          <motion.div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${(currentIndex / (commits.length - 1)) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Commit markers */}
        <div className="relative h-full">
          {commits.map((commit, index) => {
            const position = getTimelinePosition(commit.date)
            const isActive = index === currentIndex
            
            return (
              <button
                key={commit.id}
                className="absolute transform -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${position}%`, top: '50%' }}
                onClick={() => handleCommitClick(commit, index)}
                onMouseEnter={() => setCurrentCommit(commit)}
                onMouseLeave={() => setCurrentCommit(commits[currentIndex])}
              >
                <motion.div
                  className={cn(
                    "w-3 h-3 rounded-full transition-all cursor-pointer",
                    getCommitColor(index),
                    isActive ? 'w-5 h-5' : 'hover:w-4 hover:h-4'
                  )}
                  animate={{
                    scale: isActive ? 1.5 : 1,
                    boxShadow: isActive 
                      ? '0 0 20px rgba(59, 130, 246, 0.8)' 
                      : '0 0 0 rgba(0,0,0,0)'
                  }}
                  transition={{ duration: 0.2 }}
                />
              </button>
            )
          })}
        </div>

        {/* Current time indicator */}
        <div 
          className="absolute top-1/2 transform -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${(currentIndex / (commits.length - 1)) * 100}%` }}
        >
          <div className="w-1 h-8 bg-white rounded-full" />
        </div>

        {/* Time labels */}
        {commits.length > 0 && (
          <>
            <div className="absolute top-0 left-0 text-xs text-gray-400 mt-2">
              {formatDate(commits[0].date)}
            </div>
            <div className="absolute top-0 right-0 text-xs text-gray-400 mt-2">
              {formatDate(commits[commits.length - 1].date)}
            </div>
          </>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mt-6">
        <div className="flex items-center gap-4">
          {/* Play/Pause */}
          <button
            onClick={handlePlayPause}
            className="p-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full hover:opacity-90 transition-all"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5 text-white" />
            ) : (
              <Play className="w-5 h-5 text-white" />
            )}
          </button>

          {/* Skip buttons */}
          <button
            onClick={handleSkipBack}
            className="p-2 glass-dark rounded-lg hover:bg-white/20 transition-all"
            disabled={currentIndex === 0}
          >
            <SkipBack className="w-5 h-5 text-white" />
          </button>
          <button
            onClick={handleSkipForward}
            className="p-2 glass-dark rounded-lg hover:bg-white/20 transition-all"
            disabled={currentIndex === commits.length - 1}
          >
            <SkipForward className="w-5 h-5 text-white" />
          </button>

          {/* Speed controls */}
          <div className="flex items-center gap-2 ml-4">
            <span className="text-sm text-gray-400">Speed:</span>
            {(['slow', 'normal', 'fast'] as const).map((s) => (
              <button
                key={s}
                onClick={() => onSpeedChange?.(s)}
                className={cn(
                  "px-3 py-1 rounded-lg text-sm transition-all",
                  speed === s 
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white' 
                    : 'glass-dark text-gray-300 hover:bg-white/20'
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Slider */}
        <div className="flex-1 max-w-md">
          <input
            type="range"
            min="0"
            max={Math.max(0, commits.length - 1)}
            value={currentIndex}
            onChange={handleSliderChange}
            onMouseDown={() => setScrubbing(true)}
            onMouseUp={() => setScrubbing(false)}
            onTouchStart={() => setScrubbing(true)}
            onTouchEnd={() => setScrubbing(false)}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-gradient-to-r [&::-webkit-slider-thumb]:from-blue-500 [&::-webkit-slider-thumb]:to-purple-500"
          />
        </div>
      </div>

      {/* Current commit info */}
      <AnimatePresence>
        {currentCommit && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-6 glass-dark rounded-xl p-6"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <GitCommit className="w-5 h-5 text-blue-400" />
                  <div className="flex items-center gap-2">
                    <code className="px-2 py-1 bg-gray-800 rounded text-sm font-mono">
                      {currentCommit.sha.slice(0, 8)}
                    </code>
                    <span className="text-sm text-gray-400">by {currentCommit.author}</span>
                  </div>
                </div>
                
                <h4 className="text-lg font-semibold text-white mb-4">
                  {currentCommit.message}
                </h4>
                
                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-300">
                      {formatDate(currentCommit.date)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-300">
                      {currentCommit.files_changed} files
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-green-400">
                        +{currentCommit.insertions}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-red-400">
                        -{currentCommit.deletions}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Progress indicator */}
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-1">
                  {currentIndex + 1} / {commits.length}
                </div>
                <div className="text-sm text-gray-400">
                  {Math.round((currentIndex / Math.max(1, commits.length - 1)) * 100)}% complete
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Stats summary */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <div className="glass-dark rounded-xl p-4">
          <div className="text-sm text-gray-400 mb-1">Total Commits</div>
          <div className="text-2xl font-bold text-white">{commits.length}</div>
        </div>
        <div className="glass-dark rounded-xl p-4">
          <div className="text-sm text-gray-400 mb-1">Total Changes</div>
          <div className="text-2xl font-bold text-white">
            {commits.reduce((sum, commit) => sum + commit.insertions + commit.deletions, 0)}
          </div>
        </div>
        <div className="glass-dark rounded-xl p-4">
          <div className="text-sm text-gray-400 mb-1">Time Span</div>
          <div className="text-2xl font-bold text-white">
            {commits.length > 1 
              ? `${Math.round((new Date(commits[commits.length - 1].date).getTime() - new Date(commits[0].date).getTime()) / (1000 * 60 * 60 * 24))}d`
              : '0d'
            }
          </div>
        </div>
        <div className="glass-dark rounded-xl p-4">
          <div className="text-sm text-gray-400 mb-1">Current Position</div>
          <div className="text-2xl font-bold text-white">
            {formatDate(currentCommit?.date || commits[0]?.date || new Date().toISOString())}
          </div>
        </div>
      </div>
    </div>
  )
}