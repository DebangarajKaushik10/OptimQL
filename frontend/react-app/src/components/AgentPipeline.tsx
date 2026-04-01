import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Search, Zap, CheckCircle2, XCircle, Loader2 } from 'lucide-react'

export type AgentState = 'idle' | 'running' | 'done' | 'error'

interface AgentPipelineProps {
  isOptimizing: boolean
  hasResults: boolean
  isRejected: boolean
}

export function AgentPipeline({ isOptimizing, hasResults, isRejected }: AgentPipelineProps) {
  const steps = [
    { id: 'safety', label: 'Safety', icon: Shield },
    { id: 'analysis', label: 'Analysis', icon: Search },
    { id: 'optimization', label: 'Optimization', icon: Zap },
    { id: 'validation', label: 'Validation', icon: CheckCircle2 },
  ]

  const [currentStepIndex, setCurrentStepIndex] = useState(-1)

  useEffect(() => {
    if (!isOptimizing && !hasResults) {
      setCurrentStepIndex(-1)
      return
    }

    if (hasResults) {
      setCurrentStepIndex(steps.length)
      return
    }

    if (isOptimizing) {
      // Simulate sequential progress
      setCurrentStepIndex(0)
      const timings = [500, 1500, 2500, 3500]
      const timeouts = timings.map((time, index) => 
        setTimeout(() => setCurrentStepIndex(index), time)
      )
      return () => timeouts.forEach(clearTimeout)
    }
  }, [isOptimizing, hasResults])

  const getStepState = (index: number): AgentState => {
    if (!isOptimizing && !hasResults) return 'idle'
    if (hasResults) {
      if (isRejected && index >= 2) return 'error' // Suppose safety/analysis caught it, or validation failed
      return 'done'
    }
    if (index < currentStepIndex) return 'done'
    if (index === currentStepIndex) return 'running'
    return 'idle'
  }

  return (
    <div className="w-full py-8">
      <div className="flex items-center justify-between relative max-w-3xl mx-auto">
        {/* Connecting Lines Context */}
        <div className="absolute left-0 right-0 top-1/2 h-[2px] -translate-y-1/2 bg-white/5 z-0 rounded-full overflow-hidden">
          {isOptimizing && currentStepIndex >= 0 && (
            <motion.div 
              className="h-full bg-gradient-to-r from-violet-600 via-cyan-400 to-transparent"
              initial={{ width: "0%" }}
              animate={{ width: `${(currentStepIndex / (steps.length - 1)) * 100}%` }}
              transition={{ ease: "linear", duration: 0.5 }}
            />
          )}
          {hasResults && !isRejected && (
            <div className="h-full bg-emerald-500 w-full" />
          )}
          {hasResults && isRejected && (
            <div className={`h-full bg-rose-500`} style={{ width: '50%' }} />
          )}
        </div>

        {steps.map((step, index) => {
          const state = getStepState(index)
          const Icon = step.icon

          let bgColor = "bg-[#0F1623] border-white/10 text-zinc-500"
          let iconContent = <Icon className="w-5 h-5" />

          if (state === 'running') {
            bgColor = "bg-violet-900/40 border-violet-500 text-violet-400 shadow-[0_0_20px_rgba(124,58,237,0.4)]"
            iconContent = <Loader2 className="w-5 h-5 animate-spin" />
          } else if (state === 'done') {
            bgColor = "bg-emerald-900/30 border-emerald-500 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
            iconContent = <CheckCircle2 className="w-5 h-5" />
          } else if (state === 'error') {
            bgColor = "bg-rose-900/30 border-rose-500 text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.3)]"
            iconContent = <XCircle className="w-5 h-5" />
          }

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center gap-3">
              <motion.div 
                layout
                className={`w-12 h-12 rounded-[4px] flex items-center justify-center border backdrop-blur-md transition-colors duration-300 ${bgColor}`}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                {iconContent}
              </motion.div>
              <div className="absolute top-14 whitespace-nowrap">
                <span className={`text-xs font-semibold uppercase tracking-wider ${state === 'running' ? 'text-violet-400' : state === 'done' ? 'text-emerald-500' : state === 'error' ? 'text-rose-500' : 'text-zinc-500'}`}>
                  {step.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AgentPipeline
