"use client"

import React, { useRef, useState, useMemo, useCallback, Suspense } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Text, Billboard, Line, Box, Sphere, MeshDistortMaterial, Html } from '@react-three/drei'
import { Vector3, Color, Group, BufferGeometry } from 'three'
import { cn } from '@/lib/utils'

interface FileNode {
  id: string
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  complexity?: number
  children?: FileNode[]
  commits?: number
  contributors?: number
  lastModified?: string
}

interface FileTreeProps {
  data: FileNode
  onNodeClick?: (node: FileNode) => void
  selectedNode?: FileNode | null
  depth?: number
  maxDepth?: number
  showLabels?: boolean
  animate?: boolean
}

function FileNode3D({ 
  node, 
  position, 
  onClick,
  isSelected,
  showLabel,
  depth = 0,
  maxDepth = 3 
}: { 
  node: FileNode
  position: Vector3
  onClick: (node: FileNode) => void
  isSelected: boolean
  showLabel: boolean
  depth: number
  maxDepth: number
}) {
  const meshRef = useRef<Group>(null)
  const [hovered, setHovered] = useState(false)
  
  // Calculate size based on file properties
  const size = useMemo(() => {
    if (node.type === 'directory') {
      return 1.2 + Math.log((node.children?.length || 1) + 1) * 0.5
    }
    return 0.8 + Math.log((node.size || 1) / 1000 + 1) * 0.3
  }, [node])

  // Calculate color based on complexity and activity
  const color = useMemo(() => {
    const hue = (node.complexity || 0) * 60
    const saturation = 0.7
    const lightness = 0.5 + (node.commits || 0) / 1000 * 0.3
    
    return new Color(`hsl(${hue}, ${saturation * 100}%, ${lightness * 100}%)`)
  }, [node])

  // Animation
  useFrame((state) => {
    if (meshRef.current && hovered) {
      meshRef.current.rotation.y += 0.01
      meshRef.current.position.y = position.y + Math.sin(state.clock.elapsedTime) * 0.1
    } else if (meshRef.current) {
      meshRef.current.rotation.y += 0.002
    }
  })

  const handleClick = useCallback(() => {
    onClick(node)
  }, [node, onClick])

  return (
    <group position={position}>
      <group
        ref={meshRef}
        onClick={handleClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        scale={hovered || isSelected ? 1.2 : 1}
      >
        {node.type === 'directory' ? (
          <Box args={[size, size, size]}>
            <MeshDistortMaterial
              color={color}
              speed={1}
              distort={hovered ? 0.3 : 0.1}
              radius={1}
              roughness={0.3}
              metalness={0.6}
              envMapIntensity={0.5}
            />
          </Box>
        ) : (
          <Sphere args={[size * 0.8, 32, 32]}>
            <MeshDistortMaterial
              color={color}
              speed={1}
              distort={hovered ? 0.2 : 0.05}
              radius={1}
              roughness={0.5}
              metalness={0.8}
              envMapIntensity={0.8}
            />
          </Sphere>
        )}
        
        {/* Glow effect for selected nodes */}
        {isSelected && (
          <Sphere args={[size * 1.2, 16, 16]}>
            <meshBasicMaterial color={color} transparent opacity={0.2} />
          </Sphere>
        )}
      </group>

      {/* Node label */}
      {showLabel && (
        <Billboard position={[0, size + 0.3, 0]}>
          <Text
            fontSize={0.3}
            color="white"
            anchorX="center"
            anchorY="bottom"
            outlineWidth={0.02}
            outlineColor="#000"
            maxWidth={2}
            lineHeight={1}
            textAlign="center"
          >
            {node.name.length > 15 ? `${node.name.slice(0, 12)}...` : node.name}
          </Text>
          
          {/* File info */}
          <Html position={[0, -0.5, 0]} center>
            <div className="bg-black/80 backdrop-blur-sm rounded-lg p-2 text-xs text-white whitespace-nowrap">
              <div className="font-semibold">{node.name}</div>
              {node.size && (
                <div className="text-gray-300">
                  {(node.size / 1024).toFixed(1)} KB
                </div>
              )}
              {node.complexity && (
                <div className="text-gray-300">
                  Complexity: {node.complexity.toFixed(1)}
                </div>
              )}
            </div>
          </Html>
        </Billboard>
      )}
    </group>
  )
}

function ConnectionLine({ 
  start, 
  end,
  color 
}: { 
  start: Vector3
  end: Vector3
  color: string
}) {
  const lineRef = useRef<BufferGeometry>(null)
  
  useMemo(() => {
    if (lineRef.current) {
      lineRef.current.setFromPoints([start, end])
    }
  }, [start, end])

  return (
    <Line
      points={[start, end]}
      color={color}
      lineWidth={1}
      dashed={false}
      opacity={0.6}
      transparent
    />
  )
}

function TreeStructure3D({ 
  data: node, 
  position = new Vector3(0, 0, 0),
  onClick,
  selectedNode,
  depth = 0,
  maxDepth = 3,
  showLabels = true
}: FileTreeProps & {
  position?: Vector3
  onClick: (node: FileNode) => void
}) {
  const nodes = useRef<{ [key: string]: Vector3 }>({})
  const connections = useRef<Array<{ start: Vector3; end: Vector3; color: string }>>([])

  // Layout algorithm: circular layout for directories
  const layoutChildren = useCallback((children: FileNode[], parentPos: Vector3, radius = 3) => {
    const angleStep = (2 * Math.PI) / children.length
    
    return children.map((child, index) => {
      const angle = index * angleStep
      const x = parentPos.x + Math.cos(angle) * radius
      const z = parentPos.z + Math.sin(angle) * radius
      const y = parentPos.y - 2
      
      const childPos = new Vector3(x, y, z)
      nodes.current[child.id] = childPos
      
      // Store connection
      connections.current.push({
        start: parentPos,
        end: childPos,
        color: child.type === 'directory' ? '#3b82f6' : '#8b5cf6'
      })
      
      return { child, position: childPos }
    })
  }, [])

  const childrenPositions = useMemo(() => {
    if (depth >= maxDepth || !node.children?.length) return []
    return layoutChildren(node.children, position, 2 + depth * 1.5)
  }, [node.children, position, depth, maxDepth, layoutChildren])

  return (
    <>
      {/* Render current node */}
      <FileNode3D
        node={node}
        position={position}
        onClick={onClick}
        isSelected={selectedNode?.id === node.id}
        showLabel={showLabels && depth <= 2}
        depth={depth}
        maxDepth={maxDepth}
      />
      
      {/* Render connections */}
      {connections.current.map((conn, index) => (
        <ConnectionLine
          key={index}
          start={conn.start}
          end={conn.end}
          color={conn.color}
        />
      ))}
      
      {/* Recursively render children */}
      {childrenPositions.map(({ child, position: childPos }) => (
        <TreeStructure3D
          key={child.id}
          data={child}
          position={childPos}
          onClick={onClick}
          selectedNode={selectedNode}
          depth={depth + 1}
          maxDepth={maxDepth}
          showLabels={showLabels}
        />
      ))}
    </>
  )
}

function CameraController() {
  const { camera } = useThree()
  
  useFrame(() => {
    // Smooth camera movement
    camera.lookAt(0, 0, 0)
  })
  
  return null
}

interface FileTreeCanvasProps {
  data: FileNode
  onNodeClick?: (node: FileNode) => void
  selectedNode?: FileNode | null
  className?: string
}

export function FileTreeCanvas({ 
  data, 
  onNodeClick, 
  selectedNode, 
  className 
}: FileTreeCanvasProps) {
  const [showLabels, setShowLabels] = useState(true)
  const [autoRotate, setAutoRotate] = useState(true)
  
  const handleNodeClick = useCallback((node: FileNode) => {
    onNodeClick?.(node)
  }, [onNodeClick])

  return (
    <div className={cn("relative w-full h-full rounded-xl overflow-hidden", className)}>
      <Canvas
        shadows
        camera={{ position: [10, 10, 10], fov: 60 }}
        style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#8b5cf6" />
          
          <TreeStructure3D
            data={data}
            onClick={handleNodeClick}
            selectedNode={selectedNode}
            maxDepth={3}
            showLabels={showLabels}
          />
          
          <OrbitControls
            enableZoom
            enablePan
            enableRotate
            autoRotate={autoRotate}
            autoRotateSpeed={0.5}
            minDistance={5}
            maxDistance={50}
          />
          
          <CameraController />
          
          {/* Fog for depth effect */}
          <fog attach="fog" args={['#000428', 5, 30]} />
        </Suspense>
      </Canvas>
      
      {/* Controls overlay */}
      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={() => setShowLabels(!showLabels)}
          className="glass-dark px-3 py-2 rounded-lg text-sm font-medium transition-all hover:bg-white/20"
        >
          {showLabels ? 'Hide Labels' : 'Show Labels'}
        </button>
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className="glass-dark px-3 py-2 rounded-lg text-sm font-medium transition-all hover:bg-white/20"
        >
          {autoRotate ? 'Stop Rotate' : 'Auto Rotate'}
        </button>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 glass-dark p-4 rounded-lg backdrop-blur-sm">
        <div className="text-sm font-semibold text-white mb-2">Legend</div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span className="text-xs text-gray-300">Directories</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
          <span className="text-xs text-gray-300">Files</span>
        </div>
        <div className="mt-2 text-xs text-gray-400">
          Size = File size • Color = Complexity
        </div>
      </div>
    </div>
  )
}
