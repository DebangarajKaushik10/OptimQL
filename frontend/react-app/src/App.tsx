import React, { useState } from 'react'
import { QueryEditor } from './components/QueryEditor'
import { OptimizationResults, Suggestion } from './components/OptimizationResults'
import { PerformanceMetrics, Metrics } from './components/PerformanceMetrics'
import { Button } from './components/ui/button'
import { Play, Download, Copy, Terminal } from 'lucide-react'
import { toast } from './utils/toast'

export default function App() {
  const [query, setQuery] = useState('')
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [optimizedQuery, setOptimizedQuery] = useState('')
  const [metrics, setMetrics] = useState<Metrics>({
    executionTime: '0ms',
    rowsScanned: '0',
    improvement: '0%',
    complexity: 'N/A',
  })

  const exampleQuery = `SELECT * FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
AND o.status = 'completed'`

  const optimizeQuery = async () => {
    if (!query.trim()) {
      toast.error('Please enter a SQL query to optimize')
      return
    }

    setIsOptimizing(true)

    try {
      const payload = query.trim().endsWith(';') ? query.trim().slice(0, -1) : query.trim()
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: payload }),
      })
      if (!res.ok) {
        const text = await res.text()
        toast.error(`Backend error: ${text}`)
        setIsOptimizing(false)
        return
      }
      const result = await res.json()

      // Map backend result to UI state (attempt best-effort)
      setSuggestions([
        {
          type: result.best_suggestion ? 'success' : 'info',
          title: result.best_suggestion ? 'Index suggested' : 'No index suggested',
          description: result.details || '',
        },
      ])

      setOptimizedQuery(result.best_suggestion || '')
      setMetrics({
        executionTime: `${result.baseline_time_ms || 'N/A'} ms`,
        rowsScanned: result.rows_scanned || 'N/A',
        improvement: `${result.improvement_percentage || 0}%`,
        complexity: 'Unknown',
      })

      setHasResults(true)
    } catch (err) {
      toast.error(String(err))
    } finally {
      setIsOptimizing(false)
    }
  }

  const loadExample = () => {
    setQuery(exampleQuery)
    toast('Example query loaded')
  }

  const copyOptimizedQuery = async () => {
    if (optimizedQuery) {
      await navigator.clipboard.writeText(optimizedQuery)
      toast('Optimized query copied to clipboard')
    }
  }

  const downloadResults = () => {
    if (!hasResults) return
    const results = { originalQuery: query, optimizedQuery, suggestions, metrics }
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'sql-optimization-results.json'
    a.click()
    toast('Results downloaded')
  }

  return (
    <div className="min-h-screen bg-black text-zinc-100">
      
      <header className="border-b border-zinc-800">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Terminal className="h-7 w-7 text-zinc-100" strokeWidth={1.5} />
              <div>
                <h1 className="text-xl font-light text-zinc-100">SQL Optimizer</h1>
              </div>
            </div>
            <button onClick={loadExample} className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
              Load example
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-16">
        <div className="max-w-5xl mx-auto space-y-16">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-5xl font-light tracking-tight">Optimize your SQL queries</h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto font-light">
              Analyze and improve database query performance with Python-powered optimization
            </p>
          </div>

          <div className="space-y-6">
            <QueryEditor value={query} onChange={setQuery} placeholder="SELECT * FROM users WHERE ..." />

            <div className="flex gap-3">
              <Button onClick={optimizeQuery} disabled={isOptimizing} className="bg-zinc-100 text-black hover:bg-zinc-200 rounded-none font-normal">
                <Play className="mr-2 h-4 w-4" />
                {isOptimizing ? 'Optimizing...' : 'Optimize'}
              </Button>

              {hasResults && (
                <>
                  <Button variant="outline" onClick={copyOptimizedQuery} className="border-zinc-800 text-zinc-100 hover:bg-zinc-900 hover:text-zinc-100 rounded-none font-normal">
                    <Copy className="mr-2 h-4 w-4" />
                    Copy
                  </Button>
                  <Button variant="outline" onClick={downloadResults} className="border-zinc-800 text-zinc-100 hover:bg-zinc-900 hover:text-zinc-100 rounded-none font-normal">
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </>
              )}
            </div>
          </div>

          {hasResults && (
            <>
              <div className="space-y-6">
                <div className="text-sm text-zinc-400">Performance Metrics</div>
                <PerformanceMetrics metrics={metrics} />
              </div>

              <div>
                <OptimizationResults suggestions={suggestions} optimizedQuery={optimizedQuery} />
              </div>
            </>
          )}

          {!hasResults && (
            <div className="border border-dashed border-zinc-800 p-16 text-center">
              <div className="space-y-3">
                <Terminal className="h-12 w-12 text-zinc-700 mx-auto" strokeWidth={1.5} />
                <h3 className="text-lg font-light text-zinc-400">Enter a query to get started</h3>
                <p className="text-sm text-zinc-600 max-w-md mx-auto">
                  Paste your SQL query above and click optimize to receive performance insights and optimization recommendations
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-zinc-800 mt-24">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-center text-sm text-zinc-600">
            <p>Powered by Python</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
