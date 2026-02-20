import React from 'react'
import { TrendingDown, Clock, Database, Zap } from 'lucide-react'

export interface Metrics {
  executionTime: string
  rowsScanned: string
  improvement: string
  complexity: string
}

interface PerformanceMetricsProps {
  metrics: Metrics
}

export function PerformanceMetrics({ metrics }: PerformanceMetricsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="border border-zinc-800 p-6 bg-zinc-950/50">
        <div className="flex items-center gap-2 mb-3">
          <Clock className="h-4 w-4 text-zinc-400" />
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Time</div>
        </div>
        <div className="text-2xl font-light text-zinc-100">{metrics.executionTime}</div>
      </div>

      <div className="border border-zinc-800 p-6 bg-zinc-950/50">
        <div className="flex items-center gap-2 mb-3">
          <Database className="h-4 w-4 text-zinc-400" />
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Rows</div>
        </div>
        <div className="text-2xl font-light text-zinc-100">{metrics.rowsScanned}</div>
      </div>

      <div className="border border-zinc-800 p-6 bg-zinc-950/50">
        <div className="flex items-center gap-2 mb-3">
          <TrendingDown className="h-4 w-4 text-zinc-400" />
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Faster</div>
        </div>
        <div className="text-2xl font-light text-zinc-100">{metrics.improvement}</div>
      </div>

      <div className="border border-zinc-800 p-6 bg-zinc-950/50">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="h-4 w-4 text-zinc-400" />
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Complexity</div>
        </div>
        <div className="text-2xl font-light text-zinc-100">{metrics.complexity}</div>
      </div>
    </div>
  )
}

export default PerformanceMetrics
