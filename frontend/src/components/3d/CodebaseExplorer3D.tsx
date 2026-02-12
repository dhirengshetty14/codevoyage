"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Canvas, useFrame, useThree } from "@react-three/fiber"
import { Html, OrbitControls, Stars } from "@react-three/drei"
import * as THREE from "three"
import { cn } from "@/lib/utils"

type TreeNode = {
  name: string
  path: string
  type: "file" | "directory"
  size?: number
  children?: TreeNode[]
}

type ComplexityMetric = {
  path?: string
  cyclomatic_complexity?: number
}

type TimePoint = {
  date: string
  commit_sha: string
  author: string
  cumulative_commits: number
  day_commits?: number
  day_changes?: number
  rolling_7d_commits?: number
}

type ColorMode = "complexity" | "activity" | "size"
type DensityMode = "focused" | "balanced" | "full"

type FlatNode = {
  id: string
  name: string
  path: string
  parentPath: string | null
  depth: number
  topGroup: string
  type: "file" | "directory"
  ownSizeBytes: number
  aggregateSizeBytes: number
  aggregateFiles: number
  childCount: number
  complexity: number
  activity: number
  importance: number
  revealWeight: number
  position: THREE.Vector3
}

type RawNode = Omit<
  FlatNode,
  "complexity" | "activity" | "importance" | "revealWeight" | "position" | "aggregateFiles" | "aggregateSizeBytes"
>

type Edge = {
  from: THREE.Vector3
  to: THREE.Vector3
  emphasis: "low" | "high"
}

function normalizePath(value: string): string {
  const normalized = String(value || "")
    .replaceAll("\\", "/")
    .replace(/^\.?\//, "")
    .replace(/\/+/g, "/")
    .trim()
  return normalized || "root"
}

function splitPath(path: string): string[] {
  return normalizePath(path)
    .split("/")
    .filter((segment) => segment && segment !== ".")
}

function hashPath(path: string): number {
  let hash = 2166136261
  for (let i = 0; i < path.length; i += 1) {
    hash ^= path.charCodeAt(i)
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24)
  }
  return Math.abs(hash >>> 0)
}

function flattenTree(root?: TreeNode | null): RawNode[] {
  if (!root || !root.type) return []
  const nodes: RawNode[] = []

  const visit = (node: TreeNode, depth: number, parentPath: string | null) => {
    const currentPath =
      depth === 0
        ? "root"
        : normalizePath(node.path || (parentPath ? `${parentPath}/${node.name}` : node.name || "node"))
    const segments = splitPath(currentPath)
    const topGroup = depth === 0 ? "root" : segments[0] || "misc"

    nodes.push({
      id: currentPath,
      name: String(node.name || "unknown"),
      path: currentPath,
      parentPath,
      depth,
      topGroup,
      type: node.type,
      ownSizeBytes: Number(node.size || 0),
      childCount: node.type === "directory" ? (node.children?.length || 0) : 0,
    })

    if (node.type === "directory" && node.children?.length) {
      for (const child of node.children) {
        visit(child, depth + 1, currentPath)
      }
    }
  }

  visit(root, 0, null)
  return nodes
}

function layoutNodes(rawNodes: RawNode[], complexityByPath: Map<string, number>): FlatNode[] {
  if (!rawNodes.length) return []

  const byPath = new Map(rawNodes.map((node) => [node.path, node] as const))
  const aggregateSize = new Map<string, number>()
  const aggregateFiles = new Map<string, number>()

  for (const node of rawNodes) {
    aggregateSize.set(node.path, node.type === "file" ? Math.max(1, node.ownSizeBytes) : 0)
    aggregateFiles.set(node.path, node.type === "file" ? 1 : 0)
  }

  const depthSorted = [...rawNodes].sort((a, b) => b.depth - a.depth)
  for (const node of depthSorted) {
    if (!node.parentPath) continue
    if (!byPath.has(node.parentPath)) continue
    aggregateSize.set(node.parentPath, (aggregateSize.get(node.parentPath) || 0) + (aggregateSize.get(node.path) || 0))
    aggregateFiles.set(node.parentPath, (aggregateFiles.get(node.parentPath) || 0) + (aggregateFiles.get(node.path) || 0))
  }

  const depthOneGroups = rawNodes.filter((node) => node.depth === 1).map((node) => node.topGroup)
  const groupNames = Array.from(new Set(depthOneGroups)).sort((a, b) => a.localeCompare(b))
  const groupCenter = new Map<string, THREE.Vector3>()

  if (groupNames.length) {
    const radius = Math.max(10, Math.min(22, 8 + groupNames.length * 0.4))
    groupNames.forEach((group, index) => {
      const angle = (index / groupNames.length) * Math.PI * 2
      groupCenter.set(group, new THREE.Vector3(Math.cos(angle) * radius, 1.8, Math.sin(angle) * radius))
    })
  }

  const maxComplexity = Math.max(1, ...Array.from(complexityByPath.values(), (value) => Number(value || 0)))
  const maxSize = Math.max(1, ...rawNodes.map((node) => aggregateSize.get(node.path) || 0))
  const maxDepth = Math.max(1, ...rawNodes.map((node) => node.depth))

  const positioned: FlatNode[] = rawNodes.map((node) => {
    const complexity = Number(complexityByPath.get(node.path) || 0)
    const sizeValue = aggregateSize.get(node.path) || 0
    const filesValue = aggregateFiles.get(node.path) || 0
    const sizeNorm = Math.min(1, Math.log2(sizeValue + 2) / Math.log2(maxSize + 2))
    const complexityNorm = Math.min(1, complexity / maxComplexity)
    const activity = Math.min(1, complexityNorm * 0.68 + sizeNorm * 0.32)

    let position: THREE.Vector3
    if (node.depth === 0) {
      position = new THREE.Vector3(0, 3.1, 0)
    } else if (node.depth === 1) {
      const anchor = groupCenter.get(node.topGroup) || new THREE.Vector3(0, 1.8, 0)
      position = anchor.clone()
    } else {
      const anchor = groupCenter.get(node.topGroup) || new THREE.Vector3(0, 1.8, 0)
      const seed = hashPath(node.path)
      const baseAngle = ((seed % 3600) / 3600) * Math.PI * 2 + node.depth * 0.35
      const spread = 1.4 + Math.min(3.4, node.depth * 0.75) + ((seed >> 9) % 1000) / 1000
      const clusterJitter = ((seed >> 17) % 1000) / 1000
      const radius = spread + clusterJitter * (1 + node.depth * 0.2)
      const verticalJitter = (((seed >> 21) % 1000) / 1000 - 0.5) * 0.45
      const y = 2.0 - node.depth * 0.52 + verticalJitter

      position = new THREE.Vector3(
        anchor.x + Math.cos(baseAngle) * radius,
        y,
        anchor.z + Math.sin(baseAngle) * radius
      )
    }

    const depthPenalty = (maxDepth - node.depth) * 0.35
    const importance = complexity * 24 + Math.log2(sizeValue + 2) * 3.2 + depthPenalty + (node.type === "directory" ? 4.5 : 0)
    const revealWeight = node.depth * 1_000_000 + (hashPath(node.path) % 1_000_000)

    return {
      ...node,
      aggregateSizeBytes: sizeValue,
      aggregateFiles: filesValue,
      complexity,
      activity,
      importance,
      revealWeight,
      position,
    }
  })

  return positioned
}

function SceneFocusController({
  controlsRef,
  focusPoint,
  focusNonce,
}: {
  controlsRef: React.MutableRefObject<any>
  focusPoint?: THREE.Vector3
  focusNonce: number
}) {
  const { camera } = useThree()
  const remainingFrames = useRef(0)

  useEffect(() => {
    if (!focusPoint) return
    remainingFrames.current = 95
  }, [focusPoint, focusNonce])

  useFrame(() => {
    if (!focusPoint) return
    if (remainingFrames.current <= 0) return
    remainingFrames.current -= 1

    const direction = new THREE.Vector3(1.4, 0.82, 1.25).normalize()
    const targetPosition = focusPoint.clone().add(direction.multiplyScalar(6.8))
    camera.position.lerp(targetPosition, 0.11)
    if (controlsRef.current?.target) {
      controlsRef.current.target.lerp(focusPoint, 0.13)
      controlsRef.current.update()
    }
  })

  return null
}

function NodeMesh({
  node,
  selected,
  showLabels,
  colorMode,
  maxComplexity,
  maxActivity,
  maxSize,
  onSelect,
}: {
  node: FlatNode
  selected: boolean
  showLabels: boolean
  colorMode: ColorMode
  maxComplexity: number
  maxActivity: number
  maxSize: number
  onSelect: (path: string) => void
}) {
  const [hovered, setHovered] = useState(false)
  const pulseRef = useRef(0)

  useFrame((state) => {
    if (!selected) return
    pulseRef.current = 0.92 + Math.sin(state.clock.elapsedTime * 2.7) * 0.08
  })

  const color = useMemo(() => {
    const complexityNorm = maxComplexity > 0 ? node.complexity / maxComplexity : 0
    const activityNorm = maxActivity > 0 ? node.activity / maxActivity : 0
    const sizeNorm = maxSize > 0 ? Math.log2(node.aggregateSizeBytes + 2) / Math.log2(maxSize + 2) : 0

    let hue = 0.58
    let sat = 0.72
    let light = 0.44

    if (colorMode === "complexity") {
      hue = 0.61 - complexityNorm * 0.63
      sat = 0.9
      light = node.type === "directory" ? 0.5 : 0.41 + complexityNorm * 0.2
    } else if (colorMode === "activity") {
      hue = 0.44 - activityNorm * 0.34
      sat = 0.82
      light = node.type === "directory" ? 0.48 : 0.37 + activityNorm * 0.23
    } else {
      hue = 0.76 - sizeNorm * 0.62
      sat = 0.76
      light = node.type === "directory" ? 0.5 : 0.38 + sizeNorm * 0.24
    }
    return new THREE.Color().setHSL(hue, sat, light)
  }, [node, colorMode, maxComplexity, maxActivity, maxSize])

  const emissive = useMemo(() => color.clone().multiplyScalar(selected ? 0.5 : hovered ? 0.33 : 0.14), [color, selected, hovered])

  const scale = useMemo(() => {
    if (node.type === "directory") {
      return Math.min(0.95, 0.26 + Math.log2(node.aggregateFiles + 2) * 0.08)
    }
    const base = 0.08 + Math.log2(node.aggregateSizeBytes + 1024) * 0.035 + node.complexity * 0.008
    return Math.max(0.07, Math.min(0.55, base))
  }, [node])

  const selectedScale = selected ? scale * (pulseRef.current || 1) * 1.07 : scale

  return (
    <group position={node.position}>
      <mesh
        scale={hovered ? selectedScale * 1.15 : selectedScale}
        onPointerOver={(event) => {
          event.stopPropagation()
          setHovered(true)
          document.body.style.cursor = "pointer"
        }}
        onPointerOut={() => {
          setHovered(false)
          document.body.style.cursor = "default"
        }}
        onClick={(event) => {
          event.stopPropagation()
          onSelect(node.path)
        }}
      >
        {node.type === "directory" ? (
          <boxGeometry args={[1, 1, 1]} />
        ) : (
          <sphereGeometry args={[0.56, 12, 12]} />
        )}
        <meshStandardMaterial
          color={color}
          metalness={0.34}
          roughness={0.36}
          emissive={emissive}
          emissiveIntensity={selected ? 1.1 : hovered ? 0.85 : 0.42}
        />
      </mesh>

      {selected && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -scale * 0.7, 0]} scale={[1.2, 1.2, 1.2]}>
          <ringGeometry args={[scale * 1.05, scale * 1.35, 28]} />
          <meshBasicMaterial color="#22d3ee" transparent opacity={0.65} side={THREE.DoubleSide} />
        </mesh>
      )}

      {(hovered || selected || (showLabels && node.depth <= 1)) && (
        <Html center position={[0, scale + 0.34, 0]} distanceFactor={13}>
          <div className="rounded border border-white/20 bg-slate-900/90 px-2 py-1 text-[10px] text-slate-100 shadow-lg backdrop-blur">
            <div className="font-semibold">{node.name}</div>
            <div className="text-slate-300">
              d{node.depth} | {node.type} | {(node.aggregateSizeBytes / 1024).toFixed(1)}KB
            </div>
            {node.complexity > 0 && (
              <div className="text-amber-300">cx {node.complexity.toFixed(1)}</div>
            )}
          </div>
        </Html>
      )}
    </group>
  )
}

function EdgeCloud({ edges, showEdges }: { edges: Edge[]; showEdges: boolean }) {
  const lowEdges = useMemo(() => edges.filter((edge) => edge.emphasis === "low"), [edges])
  const highEdges = useMemo(() => edges.filter((edge) => edge.emphasis === "high"), [edges])

  const buildGeometry = (subset: Edge[]) => {
    const points: number[] = []
    subset.forEach((edge) => {
      points.push(edge.from.x, edge.from.y, edge.from.z)
      points.push(edge.to.x, edge.to.y, edge.to.z)
    })
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(points, 3))
    return geometry
  }

  const lowGeometry = useMemo(() => buildGeometry(lowEdges), [lowEdges])
  const highGeometry = useMemo(() => buildGeometry(highEdges), [highEdges])

  useEffect(
    () => () => {
      lowGeometry.dispose()
      highGeometry.dispose()
    },
    [lowGeometry, highGeometry]
  )

  if (!showEdges) return null

  return (
    <>
      <lineSegments geometry={lowGeometry}>
        <lineBasicMaterial color="#1d4ed8" transparent opacity={0.08} />
      </lineSegments>
      <lineSegments geometry={highGeometry}>
        <lineBasicMaterial color="#38bdf8" transparent opacity={0.52} />
      </lineSegments>
    </>
  )
}

export function CodebaseExplorer3D({
  fileTreeData,
  complexityMetrics,
  timePoints,
  timelineIndex,
  onTimelineIndexChange,
  className,
}: {
  fileTreeData?: TreeNode | null
  complexityMetrics?: ComplexityMetric[] | null
  timePoints: TimePoint[]
  timelineIndex: number
  onTimelineIndexChange: (index: number) => void
  className?: string
}) {
  const [selectedPath, setSelectedPath] = useState<string>("")
  const [showLabels, setShowLabels] = useState(false)
  const [showEdges, setShowEdges] = useState(true)
  const [autoRotate, setAutoRotate] = useState(false)
  const [colorMode, setColorMode] = useState<ColorMode>("complexity")
  const [densityMode, setDensityMode] = useState<DensityMode>("balanced")
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackMs, setPlaybackMs] = useState(650)
  const [focusNonce, setFocusNonce] = useState(0)
  const controlsRef = useRef<any>(null)

  const complexityByPath = useMemo(() => {
    const map = new Map<string, number>()
    for (const metric of complexityMetrics || []) {
      const path = normalizePath(String(metric.path || ""))
      if (!path || path === "root") continue
      map.set(path, Number(metric.cyclomatic_complexity || 0))
    }
    return map
  }, [complexityMetrics])

  const allNodes = useMemo(() => {
    const flattened = flattenTree(fileTreeData)
    if (!flattened.length) return []
    return layoutNodes(flattened, complexityByPath)
      .sort((a, b) => a.revealWeight - b.revealWeight)
      .slice(0, 2600)
  }, [fileTreeData, complexityByPath])

  const clampedTimelineIndex = useMemo(() => {
    if (!timePoints.length) return 0
    return Math.max(0, Math.min(timelineIndex, timePoints.length - 1))
  }, [timelineIndex, timePoints.length])

  const growthRatio = useMemo(() => {
    if (!timePoints.length) return 1
    return (clampedTimelineIndex + 1) / Math.max(1, timePoints.length)
  }, [clampedTimelineIndex, timePoints.length])

  const maxDepth = useMemo(() => Math.max(1, ...allNodes.map((node) => node.depth)), [allNodes])

  const visibleNodes = useMemo(() => {
    if (!allNodes.length) return []
    const depthGate = Math.max(1, Math.floor(growthRatio * (maxDepth + 1)))
    const directories = allNodes.filter((node) => node.type === "directory" && node.depth <= depthGate + 1)

    const fileCapByDensity: Record<DensityMode, number> = {
      focused: 380,
      balanced: 920,
      full: 1850,
    }
    const dynamicFileCap = Math.max(70, Math.floor(fileCapByDensity[densityMode] * growthRatio))
    const candidateFiles = allNodes
      .filter((node) => node.type === "file" && node.depth <= depthGate + 1)
      .sort((a, b) => b.importance - a.importance)
      .slice(0, dynamicFileCap)

    const map = new Map<string, FlatNode>()
    directories.forEach((node) => map.set(node.path, node))
    candidateFiles.forEach((node) => {
      map.set(node.path, node)
      let parentPath = node.parentPath
      while (parentPath) {
        const parentNode = allNodes.find((x) => x.path === parentPath)
        if (!parentNode) break
        map.set(parentNode.path, parentNode)
        parentPath = parentNode.parentPath
      }
    })

    if (selectedPath) {
      const selected = allNodes.find((node) => node.path === selectedPath)
      if (selected) {
        map.set(selected.path, selected)
        let parentPath = selected.parentPath
        while (parentPath) {
          const parentNode = allNodes.find((x) => x.path === parentPath)
          if (!parentNode) break
          map.set(parentNode.path, parentNode)
          parentPath = parentNode.parentPath
        }
      }
    }

    return Array.from(map.values())
  }, [allNodes, growthRatio, maxDepth, densityMode, selectedPath])

  const visibleByPath = useMemo(() => new Map(visibleNodes.map((node) => [node.path, node] as const)), [visibleNodes])

  const selectedNode = useMemo(() => visibleByPath.get(selectedPath) || null, [visibleByPath, selectedPath])

  const edges = useMemo(() => {
    if (!visibleNodes.length) return []
    const byPath = visibleByPath
    const list: Edge[] = []

    const addEdge = (child: FlatNode, emphasis: "low" | "high") => {
      if (!child.parentPath) return
      const parent = byPath.get(child.parentPath)
      if (!parent) return
      list.push({ from: parent.position, to: child.position, emphasis })
    }

    if (selectedNode) {
      const highlightPaths = new Set<string>()
      highlightPaths.add(selectedNode.path)

      let parentPath = selectedNode.parentPath
      while (parentPath) {
        highlightPaths.add(parentPath)
        parentPath = byPath.get(parentPath)?.parentPath || null
      }

      const childSlice = visibleNodes.filter((node) => node.parentPath === selectedNode.path).slice(0, 60)
      childSlice.forEach((node) => highlightPaths.add(node.path))

      if (selectedNode.parentPath) {
        visibleNodes
          .filter((node) => node.parentPath === selectedNode.parentPath && node.path !== selectedNode.path)
          .slice(0, 24)
          .forEach((node) => highlightPaths.add(node.path))
      }

      visibleNodes.forEach((node) => {
        if (!node.parentPath) return
        const important = highlightPaths.has(node.path) || highlightPaths.has(node.parentPath)
        if (!important && node.depth > 2) return
        addEdge(node, important ? "high" : "low")
      })
    } else {
      visibleNodes.forEach((node) => {
        if (!node.parentPath) return
        if (node.depth <= 2 || (node.depth <= 4 && node.type === "directory")) {
          addEdge(node, node.depth <= 2 ? "high" : "low")
        }
      })
    }

    return list.slice(0, 1200)
  }, [visibleNodes, visibleByPath, selectedNode])

  const maxComplexity = useMemo(() => Math.max(1, ...visibleNodes.map((node) => node.complexity)), [visibleNodes])
  const maxActivity = useMemo(() => Math.max(1, ...visibleNodes.map((node) => node.activity)), [visibleNodes])
  const maxSize = useMemo(() => Math.max(1, ...visibleNodes.map((node) => node.aggregateSizeBytes)), [visibleNodes])

  const hotspots = useMemo(
    () => [...visibleNodes].filter((node) => node.type === "file").sort((a, b) => b.importance - a.importance).slice(0, 8),
    [visibleNodes]
  )

  const focusOptions = useMemo(() => {
    const topDirs = allNodes.filter((node) => node.type === "directory" && node.depth <= 2)
    const topFiles = [...allNodes].filter((node) => node.type === "file").sort((a, b) => b.importance - a.importance).slice(0, 100)
    const merged = [...topDirs, ...topFiles]
    return merged.slice(0, 160)
  }, [allNodes])

  const timelinePoint = timePoints[clampedTimelineIndex] || null

  useEffect(() => {
    if (!visibleNodes.length) return
    if (selectedPath && visibleByPath.has(selectedPath)) return
    const defaultSelection = hotspots[0]?.path || visibleNodes[0]?.path || ""
    if (defaultSelection) {
      setSelectedPath(defaultSelection)
      setFocusNonce((value) => value + 1)
    }
  }, [visibleNodes, visibleByPath, selectedPath, hotspots])

  useEffect(() => {
    if (!isPlaying) return
    if (!timePoints.length) return
    const maxIndex = timePoints.length - 1
    if (clampedTimelineIndex >= maxIndex) {
      setIsPlaying(false)
      return
    }
    const timer = window.setTimeout(() => {
      onTimelineIndexChange(Math.min(maxIndex, clampedTimelineIndex + 1))
    }, playbackMs)
    return () => window.clearTimeout(timer)
  }, [isPlaying, clampedTimelineIndex, timePoints.length, playbackMs, onTimelineIndexChange])

  if (!fileTreeData || !allNodes.length) {
    return (
      <div className={cn("rounded-2xl border border-white/10 bg-white/5 p-6 text-slate-300", className)}>
        3D explorer is waiting for `file_tree_data`.
      </div>
    )
  }

  return (
    <div className={cn("rounded-2xl border border-cyan-400/20 bg-gradient-to-b from-slate-900/95 to-slate-950 p-6", className)}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-slate-100">3D Codebase Explorer</h3>
          <p className="mt-1 text-sm text-slate-300">
            Clustered by top-level modules, colored by engineering signal, and replayable over timeline.
          </p>
        </div>
        <div className="grid gap-2 text-xs md:grid-cols-2">
          <button
            onClick={() => setShowLabels((value) => !value)}
            className="rounded border border-white/20 px-2 py-1 text-slate-200 hover:bg-white/10"
          >
            {showLabels ? "Labels: ON" : "Labels: OFF"}
          </button>
          <button
            onClick={() => setShowEdges((value) => !value)}
            className="rounded border border-white/20 px-2 py-1 text-slate-200 hover:bg-white/10"
          >
            {showEdges ? "Edges: ON" : "Edges: OFF"}
          </button>
          <button
            onClick={() => setAutoRotate((value) => !value)}
            className="rounded border border-white/20 px-2 py-1 text-slate-200 hover:bg-white/10"
          >
            {autoRotate ? "Auto-Rotate: ON" : "Auto-Rotate: OFF"}
          </button>
          <button
            onClick={() => setIsPlaying((value) => !value)}
            className="rounded border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-cyan-200 hover:bg-cyan-500/20"
          >
            {isPlaying ? "Pause Replay" : "Play Replay"}
          </button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[1.2fr_1fr_1fr]">
        <div className="rounded border border-white/10 bg-black/20 p-3 text-sm text-slate-300">
          <p>Date: {timelinePoint?.date || "N/A"}</p>
          <p>Commit: {timelinePoint?.commit_sha || "N/A"}</p>
          <p>Author: {timelinePoint?.author || "N/A"}</p>
          <p>7d Velocity: {timelinePoint?.rolling_7d_commits ?? 0} commits</p>
        </div>
        <div className="rounded border border-white/10 bg-black/20 p-3 text-sm text-slate-300">
          <p>Visible Nodes: {visibleNodes.length}</p>
          <p>Visible Edges: {edges.length}</p>
          <p>Timeline Growth: {(growthRatio * 100).toFixed(1)}%</p>
          <p>Density: {densityMode.toUpperCase()}</p>
        </div>
        <div className="rounded border border-white/10 bg-black/20 p-3 text-sm text-slate-300">
          <p>Selected: {selectedNode?.path || "None"}</p>
          <p>Complexity: {selectedNode ? selectedNode.complexity.toFixed(2) : "0.00"}</p>
          <p>Files in Subtree: {selectedNode?.aggregateFiles ?? 0}</p>
          <p>Size: {selectedNode ? (selectedNode.aggregateSizeBytes / 1024).toFixed(1) : "0.0"}KB</p>
        </div>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-[1.3fr_1fr]">
        <div className="grid gap-3 md:grid-cols-[1.1fr_1fr_1fr]">
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">Zoom To Module/File</label>
            <select
              className="w-full rounded border border-white/20 bg-black/30 px-3 py-2 text-sm"
              value={selectedPath}
              onChange={(event) => {
                setSelectedPath(event.target.value)
                setFocusNonce((value) => value + 1)
              }}
            >
              {focusOptions.map((node) => (
                <option key={node.id} value={node.path}>
                  {node.path}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">Color Signal</label>
            <select
              className="w-full rounded border border-white/20 bg-black/30 px-3 py-2 text-sm"
              value={colorMode}
              onChange={(event) => setColorMode(event.target.value as ColorMode)}
            >
              <option value="complexity">Complexity</option>
              <option value="activity">Activity</option>
              <option value="size">Size</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">Scene Density</label>
            <select
              className="w-full rounded border border-white/20 bg-black/30 px-3 py-2 text-sm"
              value={densityMode}
              onChange={(event) => setDensityMode(event.target.value as DensityMode)}
            >
              <option value="focused">Focused</option>
              <option value="balanced">Balanced</option>
              <option value="full">Full</option>
            </select>
          </div>
          <div className="md:col-span-3">
            <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">History Scrub</label>
            <input
              type="range"
              min={0}
              max={Math.max(0, timePoints.length - 1)}
              value={clampedTimelineIndex}
              onChange={(event) => onTimelineIndexChange(Number(event.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div className="rounded border border-white/10 bg-black/20 p-3">
          <p className="text-sm font-semibold text-slate-200">Top Visible Hotspots</p>
          <div className="mt-2 space-y-1">
            {hotspots.slice(0, 6).map((node) => (
              <button
                key={node.id}
                onClick={() => {
                  setSelectedPath(node.path)
                  setFocusNonce((value) => value + 1)
                }}
                className={cn(
                  "w-full rounded border px-2 py-1 text-left text-xs",
                  node.path === selectedPath
                    ? "border-cyan-400/50 bg-cyan-500/10 text-cyan-200"
                    : "border-white/10 bg-white/5 text-slate-300 hover:border-white/30"
                )}
              >
                <div className="truncate font-medium">{node.path}</div>
                <div className="text-[10px] text-slate-400">cx {node.complexity.toFixed(1)} | {(node.aggregateSizeBytes / 1024).toFixed(1)}KB</div>
              </button>
            ))}
          </div>
          <div className="mt-3 text-[10px] text-slate-400">
            Replay speed:
            <button onClick={() => setPlaybackMs(900)} className={cn("ml-2 rounded px-2 py-0.5", playbackMs === 900 ? "bg-cyan-500/20 text-cyan-200" : "bg-white/5")}>
              Slow
            </button>
            <button onClick={() => setPlaybackMs(650)} className={cn("ml-1 rounded px-2 py-0.5", playbackMs === 650 ? "bg-cyan-500/20 text-cyan-200" : "bg-white/5")}>
              Normal
            </button>
            <button onClick={() => setPlaybackMs(400)} className={cn("ml-1 rounded px-2 py-0.5", playbackMs === 400 ? "bg-cyan-500/20 text-cyan-200" : "bg-white/5")}>
              Fast
            </button>
          </div>
        </div>
      </div>

      <div className="mt-4 h-[560px] overflow-hidden rounded-xl border border-cyan-500/30 bg-[#020612]">
        <Canvas camera={{ position: [16, 10, 16], fov: 48 }}>
          <color attach="background" args={["#020612"]} />
          <fog attach="fog" args={["#020612", 24, 88]} />
          <ambientLight intensity={0.45} />
          <directionalLight position={[12, 20, 9]} intensity={1.15} />
          <pointLight position={[-16, -4, -12]} intensity={0.35} color="#38bdf8" />
          <Stars radius={110} depth={36} count={1300} factor={3} saturation={0} fade speed={0.3} />

          <gridHelper args={[110, 110, "#0f172a", "#082f49"]} position={[0, -4.5, 0]} />

          <EdgeCloud edges={edges} showEdges={showEdges} />
          {visibleNodes.map((node) => (
            <NodeMesh
              key={node.id}
              node={node}
              selected={node.path === selectedPath}
              showLabels={showLabels}
              colorMode={colorMode}
              maxComplexity={maxComplexity}
              maxActivity={maxActivity}
              maxSize={maxSize}
              onSelect={(path) => {
                setSelectedPath(path)
                setFocusNonce((value) => value + 1)
              }}
            />
          ))}

          <SceneFocusController controlsRef={controlsRef} focusPoint={selectedNode?.position} focusNonce={focusNonce} />

          <OrbitControls
            ref={controlsRef}
            enablePan
            enableRotate
            enableZoom
            autoRotate={autoRotate}
            autoRotateSpeed={0.23}
            minDistance={5}
            maxDistance={95}
            dampingFactor={0.08}
            enableDamping
          />
        </Canvas>
      </div>

      <div className="mt-3 grid gap-2 text-xs md:grid-cols-3">
        <div className="rounded border border-cyan-400/20 bg-cyan-500/10 px-2 py-1 text-cyan-100">
          Structure-first layout: top-level directories become spatial clusters.
        </div>
        <div className="rounded border border-amber-400/20 bg-amber-500/10 px-2 py-1 text-amber-100">
          Signal-driven color mode: complexity, activity, or size.
        </div>
        <div className="rounded border border-emerald-400/20 bg-emerald-500/10 px-2 py-1 text-emerald-100">
          Timeline replay controls how much of the graph is revealed.
        </div>
      </div>
    </div>
  )
}
