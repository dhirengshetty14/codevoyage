import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import { Toaster } from 'react-hot-toast'
import { WebSocketProvider } from '@/lib/websocket'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CodeVoyage - 3D Codebase Visualization',
  description: 'Production-grade 3D codebase visualization and analysis platform',
  keywords: ['code visualization', 'git analysis', '3D', 'AI insights', 'codebase'],
  authors: [{ name: 'CodeVoyage Team' }],
  openGraph: {
    type: 'website',
    title: 'CodeVoyage - 3D Codebase Visualization',
    description: 'Transform your Git repositories into stunning interactive 3D visualizations',
    images: ['/og-image.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CodeVoyage - 3D Codebase Visualization',
    description: 'Production-grade 3D codebase visualization and analysis platform',
    images: ['/og-image.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-gradient-space min-h-screen antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <WebSocketProvider>
            {children}
          </WebSocketProvider>
          <Toaster
            position="top-right"
            toastOptions={{
              className: 'glass-dark',
              duration: 4000,
              style: {
                background: 'rgba(0, 0, 0, 0.8)',
                color: '#fff',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              },
            }}
          />
        </ThemeProvider>
      </body>
    </html>
  )
}