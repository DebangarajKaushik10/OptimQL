import React from 'react'
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react'

export interface Suggestion {
  type: 'success' | 'warning' | 'info'
  title: string
  description: string
}

interface OptimizationResultsProps {
  suggestions: Suggestion[]
  optimizedQuery: string
}

export function OptimizationResults({ suggestions, optimizedQuery }: OptimizationResultsProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-zinc-100" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-zinc-100" />
      case 'info':
        return <Info className="h-4 w-4 text-zinc-100" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="text-sm text-zinc-400 mb-3">Optimized Query</div>
        <pre className="bg-black text-zinc-100 p-6 overflow-x-auto font-mono text-sm border border-zinc-800">{optimizedQuery}</pre>
      </div>

      <div>
        <div className="text-sm text-zinc-400 mb-3">Suggestions ({suggestions.length})</div>
        <div className="space-y-2">
          {suggestions.map((suggestion, index) => (
            <div key={index} className="flex gap-4 p-4 border border-zinc-800 bg-zinc-950/50">
              <div className="flex-shrink-0 mt-0.5">{getIcon(suggestion.type)}</div>
              <div className="flex-1 space-y-1">
                <p className="text-sm text-zinc-100">{suggestion.title}</p>
                <p className="text-sm text-zinc-500">{suggestion.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default OptimizationResults
