"use client"

import * as React from "react"

interface ThemeProviderProps {
  children: React.ReactNode
  [key: string]: unknown
}

// Lightweight provider to avoid hard dependency on next-themes during local setup.
export function ThemeProvider({ children }: ThemeProviderProps) {
  return <>{children}</>
}
