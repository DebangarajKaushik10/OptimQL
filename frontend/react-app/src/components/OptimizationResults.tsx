import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, Info, Copy, ShieldAlert } from 'lucide-react'

export interface Suggestion {
  type: 'success' | 'warning' | 'info'
  title: string
  description: string
}

interface OptimizationResultsProps {
  originalQuery: string
  optimizedQuery: string
  suggestions: Suggestion[]
}

export function OptimizationResults({ originalQuery, optimizedQuery, suggestions }: OptimizationResultsProps) {
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: { type: "spring", bounce: 0.4, staggerChildren: 0.1 }
    }
  }

  const isRejected = suggestions.some(s => s.type === 'warning' && s.title.includes('Rejected'))

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
      
      {/* Side-by-Side Code View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Original Query */}
        <div className="flex flex-col rounded-[4px] overflow-hidden border border-white/10 bg-[#0F1623] shadow-lg">
          <div className="bg-black/40 border-b border-white/5 p-3 flex justify-between items-center">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-widest pl-2">Original</span>
          </div>
          <div className="p-4 overflow-x-auto relative group">
            <pre className="font-mono text-sm text-zinc-300/80 leading-relaxed">{originalQuery}</pre>
          </div>
        </div>

        {/* Suggested Query */}
        <div className="flex flex-col rounded-[4px] overflow-hidden border border-emerald-500/30 bg-[#0F1623] shadow-[0_0_30px_rgba(16,185,129,0.05)]">
          <div className="bg-black/40 border-b border-emerald-500/20 p-3 flex justify-between items-center">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-widest pl-2">Optimized</span>
            {optimizedQuery && (
              <button 
                onClick={() => navigator.clipboard.writeText(optimizedQuery)}
                className="text-zinc-500 hover:text-emerald-400 transition-colors bg-white/5 p-1.5 rounded-md"
              >
                <Copy className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="p-4 overflow-x-auto">
            {isRejected ? (
              <div className="h-full flex flex-col items-center justify-center py-8 text-rose-500/50">
                <ShieldAlert className="h-10 w-10 mb-3" />
                <span className="font-mono text-sm">Query Blocked. No optimization generated.</span>
              </div>
            ) : (
              <pre className="font-mono text-sm text-emerald-100 leading-relaxed">{optimizedQuery}</pre>
            )}
          </div>
        </div>
      </div>

      {/* Details Strip */}
      <div className="space-y-3">
        {suggestions.map((suggestion, index) => {
          let bg = "bg-white/5 border-white/10"
          let icon = <Info className="h-5 w-5 text-cyan-400" />
          if (suggestion.type === 'success') {
            bg = "bg-emerald-950/30 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]"
            icon = <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          } else if (suggestion.type === 'warning') {
            bg = "bg-rose-950/30 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.15)]"
            icon = <AlertTriangle className="h-5 w-5 text-rose-400" />
          }

          return (
            <motion.div 
              key={index} 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + (index * 0.1) }}
              className={`flex gap-4 p-5 rounded-2xl border backdrop-blur-sm ${bg}`}
            >
              <div className="flex-shrink-0 mt-0.5">{icon}</div>
              <div className="flex-1 space-y-1.5">
                <p className="text-sm font-semibold text-zinc-100">{suggestion.title}</p>
                <p className="text-sm text-zinc-400 leading-relaxed font-mono whitespace-pre-wrap">{suggestion.description}</p>
              </div>
            </motion.div>
          )
        })}
      </div>

    </motion.div>
  )
}

export default OptimizationResults
