// @ts-nocheck
"use client"

import React, { useRef, useEffect, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { motion } from 'framer-motion'
import { Users, GitCommit, GitBranch, Star, TrendingUp, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ContributorNode {
  id: string
  name: string
  email: string
  commits: number
  insertions: number
  deletions: number
  firstCommit: string
  lastCommit: string
  avatarUrl?: string
}

interface CollaborationLink {
  source: string
  target: string
  strength: number
  files: number
}

interface ContributorNetworkProps {
  contributors: ContributorNode[]
  collaborations: CollaborationLink[]
  selectedNode?: ContributorNode | null
  onNodeClick?: (node: ContributorNode) => void
  className?: string
}

export function ContributorNetwork({
  contributors,
  collaborations,
  selectedNode,
  onNodeClick,
  className
}: ContributorNetworkProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [hoveredNode, setHoveredNode] = useState<ContributorNode | null>(null)
  const [hoveredLink, setHoveredLink] = useState<CollaborationLink | null>(null)
  const [viewMode, setViewMode] = useState<'network' | 'radial'>('network')

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current?.parentElement) {
        const { width, height } = svgRef.current.parentElement.getBoundingClientRect()
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Create the network visualization
  useEffect(() => {
    if (!svgRef.current || contributors.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = dimensions.width
    const height = dimensions.height
    const margin = { top: 20, right: 20, bottom: 20, left: 20 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Create simulation
    const simulation = d3.forceSimulation(contributors)
      .force('link', d3.forceLink(collaborations).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(innerWidth / 2, innerHeight / 2))
      .force('collision', d3.forceCollide().radius((d: any) => Math.sqrt(d.commits) * 2 + 10))

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(collaborations)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => {
        const opacity = d.strength * 0.7 + 0.3
        return `rgba(99, 102, 241, ${opacity})`
      })
      .attr('stroke-width', (d: any) => d.strength * 3)
      .attr('stroke-opacity', 0.6)
      .on('mouseover', (event: MouseEvent, d: any) => {
        setHoveredLink(d)
      })
      .on('mouseout', () => {
        setHoveredLink(null)
      })

    // Create nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(contributors)
      .enter()
      .append('circle')
      .attr('r', (d: any) => Math.sqrt(d.commits) * 2 + 8)
      .attr('fill', (d: any) => {
        const hue = (d.commits % 10) * 36
        return d3.hsl(hue, 0.7, 0.6).toString()
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('cursor', 'pointer')
      .on('click', (event: MouseEvent, d: any) => {
        onNodeClick?.(d)
      })
      .on('mouseover', (event: MouseEvent, d: any) => {
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr('r', Math.sqrt(d.commits) * 2 + 12)
          .attr('stroke-width', 4)
        
        setHoveredNode(d)
      })
      .on('mouseout', (event: MouseEvent, d: any) => {
        d3.select(event.currentTarget)
          .transition()
          .duration(200)
          .attr('r', Math.sqrt(d.commits) * 2 + 8)
          .attr('stroke-width', 2)
        
        if (selectedNode?.id !== d.id) {
          setHoveredNode(null)
        }
      })

    // Highlight selected node
    if (selectedNode) {
      node.filter((d: any) => d.id === selectedNode.id)
        .attr('stroke', '#f59e0b')
        .attr('stroke-width', 4)
    }

    // Add labels
    const label = g.append('g')
      .selectAll('text')
      .data(contributors)
      .enter()
      .append('text')
      .text((d: any) => d.name.split(' ')[0])
      .attr('text-anchor', 'middle')
      .attr('dy', -15)
      .attr('fill', 'white')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('pointer-events', 'none')

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y)

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y)
    })

    // Zoom and drag behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom as any)

    return () => {
      simulation.stop()
    }
  }, [contributors, collaborations, dimensions, selectedNode, onNodeClick])

  const getNodeStats = useCallback((node: ContributorNode) => {
    const totalChanges = node.insertions + node.deletions
    const avgChanges = Math.round(totalChanges / Math.max(1, node.commits))
    const activity = new Date(node.lastCommit).getTime() - new Date(node.firstCommit).getTime()
    const activityDays = Math.round(activity / (1000 * 60 * 60 * 24))
    
    return { totalChanges, avgChanges, activityDays }
  }, [])

  return (
    <div className={cn("relative w-full h-full", className)}>
      {/* Visualization container */}
      <div className="relative w-full h-[600px] bg-gradient-to-br from-gray-900 to-gray-950 rounded-xl overflow-hidden">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          className="rounded-xl"
        />
        
        {/* Controls overlay */}
        <div className="absolute top-4 left-4 flex gap-2">
          <button
            onClick={() => setViewMode('network')}
            className={cn(
              "px-3 py-2 rounded-lg text-sm font-medium transition-all",
              viewMode === 'network'
                ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                : 'glass-dark text-gray-300 hover:bg-white/20'
            )}
          >
            Network View
          </button>
          <button
            onClick={() => setViewMode('radial')}
            className={cn(
              "px-3 py-2 rounded-lg text-sm font-medium transition-all",
              viewMode === 'radial'
                ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                : 'glass-dark text-gray-300 hover:bg-white/20'
            )}
          >
            Radial View
          </button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 glass-dark p-4 rounded-lg backdrop-blur-sm">
          <div className="text-sm font-semibold text-white mb-2">Network Legend</div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-xs text-gray-300">Size = Commit count</span>
          </div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-1 bg-indigo-500/60"></div>
            <span className="text-xs text-gray-300">Thickness = Collaboration strength</span>
          </div>
          <div className="text-xs text-gray-400 mt-2">
            Click on nodes to select, drag to move
          </div>
        </div>

        {/* Stats panel */}
        {(hoveredNode || selectedNode) && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="absolute top-4 right-4 glass-dark p-4 rounded-xl backdrop-blur-sm max-w-sm"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-white">
                  {(hoveredNode || selectedNode)?.name}
                </h3>
                <p className="text-sm text-gray-400">
                  {(hoveredNode || selectedNode)?.email}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="glass-dark p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <GitCommit className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-gray-400">Commits</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {(hoveredNode || selectedNode)?.commits}
                </div>
              </div>
              <div className="glass-dark p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-gray-400">Changes</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {getNodeStats((hoveredNode || selectedNode)!).totalChanges}
                </div>
              </div>
              <div className="glass-dark p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="w-4 h-4 text-purple-400" />
                  <span className="text-sm text-gray-400">Avg/Commit</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {getNodeStats((hoveredNode || selectedNode)!).avgChanges}
                </div>
              </div>
              <div className="glass-dark p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <GitBranch className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-gray-400">Activity</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {getNodeStats((hoveredNode || selectedNode)!).activityDays}d
                </div>
              </div>
            </div>

            <div className="text-xs text-gray-400">
              <div className="flex items-center gap-2 mb-1">
                <Star className="w-3 h-3" />
                <span>First commit: {new Date((hoveredNode || selectedNode)!.firstCommit).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="w-3 h-3" />
                <span>Last commit: {new Date((hoveredNode || selectedNode)!.lastCommit).toLocaleDateString()}</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Collaboration info */}
        {hoveredLink && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-20 left-1/2 transform -translate-x-1/2 glass-dark p-4 rounded-xl backdrop-blur-sm"
          >
            <div className="text-center">
              <div className="text-sm font-semibold text-white mb-2">
                Collaboration
              </div>
              <div className="text-xs text-gray-300">
                <div className="mb-1">
                  <span className="font-medium">{hoveredLink.source}</span>
                  <span className="mx-2">→</span>
                  <span className="font-medium">{hoveredLink.target}</span>
                </div>
                <div className="flex items-center justify-center gap-4">
                  <span>Strength: {Math.round(hoveredLink.strength * 100)}%</span>
                  <span>Files: {hoveredLink.files}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4 mt-4">
        <div className="glass-dark rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-blue-400" />
            <div className="text-sm text-gray-400">Total Contributors</div>
          </div>
          <div className="text-2xl font-bold text-white">{contributors.length}</div>
        </div>
        <div className="glass-dark rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <GitCommit className="w-5 h-5 text-green-400" />
            <div className="text-sm text-gray-400">Total Commits</div>
          </div>
          <div className="text-2xl font-bold text-white">
            {contributors.reduce((sum, c) => sum + c.commits, 0)}
          </div>
        </div>
        <div className="glass-dark rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <GitBranch className="w-5 h-5 text-purple-400" />
            <div className="text-sm text-gray-400">Collaborations</div>
          </div>
          <div className="text-2xl font-bold text-white">{collaborations.length}</div>
        </div>
        <div className="glass-dark rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-yellow-400" />
            <div className="text-sm text-gray-400">Avg Commits/Person</div>
          </div>
          <div className="text-2xl font-bold text-white">
            {Math.round(contributors.reduce((sum, c) => sum + c.commits, 0) / Math.max(1, contributors.length))}
          </div>
        </div>
      </div>
    </div>
  )
}
