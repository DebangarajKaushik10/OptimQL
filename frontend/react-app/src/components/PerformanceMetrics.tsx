import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingDown, Clock, Target } from 'lucide-react'

export interface Metrics {
  executionTime: string
  rowsScanned: string
  improvement: string
  confidence: string
}

interface PerformanceMetricsProps {
  metrics: Metrics
}

export function PerformanceMetrics({ metrics }: PerformanceMetricsProps) {
  const [fill, setFill] = useState(0)

  useEffect(() => {
    const improvementStr = metrics.improvement.replace('%', '')
    const val = parseFloat(improvementStr)
    const timer = setTimeout(() => {
      setFill(!isNaN(val) ? val : 0)
    }, 500)
    return () => clearTimeout(timer)
  }, [metrics])

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", bounce: 0.4 } }
  }

  return (
    <motion.div 
      variants={containerVariants} 
      initial="hidden" 
      animate="show"
      className="grid grid-cols-1 md:grid-cols-3 gap-6"
    >
      {/* Improvement Metric */}
      <motion.div variants={itemVariants} className="relative overflow-hidden border border-cyan-500/30 p-6 rounded-[4px] bg-white/5 backdrop-blur-md shadow-xl group hover:-translate-y-1 transition-transform duration-300">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent"></div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-emerald-400" />
            <div className="text-xs text-zinc-400 uppercase tracking-widest font-semibold">Improvement</div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" className="text-white/10" />
              <motion.circle 
                cx="50" cy="50" r="45" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="8" 
                strokeDasharray="283"
                initial={{ strokeDashoffset: 283 }}
                animate={{ strokeDashoffset: 283 - (fill / 100) * 283 }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                className="text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" 
              />
            </svg>
            <div className="absolute font-mono text-sm font-bold text-center text-white">{metrics.improvement}</div>
          </div>
          <div className="text-xs text-zinc-500 max-w-[120px]">
             Reduction in overall scan cost
          </div>
        </div>
      </motion.div>

      {/* Confidence Score Metric */}
      <motion.div variants={itemVariants} className="relative overflow-hidden border border-cyan-500/30 p-6 rounded-[4px] bg-white/5 backdrop-blur-md shadow-xl group hover:-translate-y-1 transition-transform duration-300">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>
        <div className="flex items-center gap-2 mb-4">
          <Target className="h-4 w-4 text-cyan-400" />
          <div className="text-xs text-zinc-400 uppercase tracking-widest font-semibold">Confidence</div>
        </div>
        <div className="flex flex-col gap-1">
          <div className="text-4xl font-mono text-white font-light tracking-tight">{metrics.confidence}</div>
          <div className="mt-2 h-2 w-full bg-white/10 rounded-full overflow-hidden">
             <div className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(6,185,212,0.8)]" style={{ width: metrics.confidence }}></div>
          </div>
        </div>
      </motion.div>

      {/* Execution Time Metric */}
      <motion.div variants={itemVariants} className="relative overflow-hidden border border-cyan-500/30 p-6 rounded-[4px] bg-white/5 backdrop-blur-md shadow-xl group hover:-translate-y-1 transition-transform duration-300">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent"></div>
        <div className="flex items-center gap-2 mb-4">
          <Clock className="h-4 w-4 text-amber-400" />
          <div className="text-xs text-zinc-400 uppercase tracking-widest font-semibold">Execution</div>
        </div>
        <div className="flex flex-col">
          <div className="text-3xl font-mono text-white tracking-tight">{metrics.executionTime}</div>
          <div className="text-sm font-mono text-amber-400/80 mt-1">Est. base time</div>
        </div>
      </motion.div>

    </motion.div>
  )
}

export default PerformanceMetrics
