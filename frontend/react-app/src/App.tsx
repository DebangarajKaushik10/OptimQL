import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { QueryEditor } from './components/QueryEditor'
import { OptimizationResults, Suggestion } from './components/OptimizationResults'
import { PerformanceMetrics, Metrics } from './components/PerformanceMetrics'
import { AgentPipeline } from './components/AgentPipeline'
import { Play, Terminal, Database, Github, Wand2, Loader2, Share2, FileJson, FileSpreadsheet, Download } from 'lucide-react'
import { toast } from './utils/toast'

export default function App() {
  const [query, setQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'analyzer' | 'history' | 'docs'>('analyzer')
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [optimizedQuery, setOptimizedQuery] = useState('')
  const [isRejected, setIsRejected] = useState(false)
  const [metrics, setMetrics] = useState<Metrics>({
    executionTime: '0ms',
    rowsScanned: '0',
    improvement: '0%',
    confidence: 'N/A',
  })
  
  const [historyLog, setHistoryLog] = useState<any[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  useEffect(() => {
    if (activeTab === 'history') {
      const fetchHistory = async () => {
        setIsLoadingHistory(true)
        try {
          const res = await fetch('http://localhost:8000/history')
          if (res.ok) {
            const data = await res.json()
            setHistoryLog(data)
          }
        } catch (e) {
          console.error(e)
        } finally {
          setIsLoadingHistory(false)
        }
      }
      fetchHistory()
    }
  }, [activeTab])

  const exampleQueries = [
    { label: "JOIN + WHERE", sql: "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > '2024-01-01' AND o.status = 'completed'" },
    { label: "Correlated Subquery", sql: "SELECT e.name, e.salary FROM employees e WHERE e.salary > (SELECT AVG(salary) FROM employees WHERE department = e.department)" },
    { label: "SELECT *", sql: "SELECT * FROM large_transactions_table" },
  ]

  const loadExample = (sql: string) => {
    setQuery(sql)
  }

  const optimizeQuery = async () => {
    if (!query.trim()) {
      toast.error('Please enter a SQL query to optimize')
      return
    }

    setIsOptimizing(true)
    setHasResults(false)

    try {
      const payload = query.trim().endsWith(';') ? query.trim().slice(0, -1) : query.trim()
      
      // We still hit the real backend, but the AgentPipeline component
      // simulates a step-by-step progress visually while we wait.
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

      const suggestedQuery = result.suggested_query || ''
      const improvementPct = result.improvement_percentage || 0
      const confidenceScore = result.confidence_score || 0
      const details = result.details || ''

      const rejected = suggestedQuery === 'N/A'
      setIsRejected(rejected)
      
      const hasImprovement = improvementPct > 0 && !rejected

      const timeMs = result.baseline_time_ms
      const rows = result.rows_scanned

      setSuggestions([
        {
          type: rejected ? 'warning' : hasImprovement ? 'success' : 'info',
          title: rejected
            ? 'Query Rejected by Safety Agent'
            : hasImprovement
              ? 'Optimization Validated'
              : 'Structural Analysis Complete',
          description: details,
        },
      ])

      setOptimizedQuery(rejected ? '' : suggestedQuery)
      setMetrics({
        executionTime: timeMs !== undefined && timeMs !== null ? `${timeMs}ms` : 'N/A',
        rowsScanned: rows !== undefined && rows !== null ? String(rows) : 'N/A',
        improvement: `${improvementPct.toFixed(1)}%`,
        confidence: `${(confidenceScore * 100).toFixed(0)}%`,
      })

      setHasResults(true)
    } catch (err) {
      toast.error(String(err))
    } finally {
      setIsOptimizing(false)
    }
  }

  const exportToJSON = () => {
    if (!hasResults) {
      toast.error('No results to export')
      return
    }
    const data = {
      originalQuery: query,
      optimizedQuery,
      isRejected,
      metrics,
      suggestions,
      timestamp: new Date().toISOString()
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `optimql-export-${Date.now()}.json`
    a.click()
    toast.success('JSON Exported')
  }

  const exportToCSV = () => {
    if (!hasResults) {
      toast.error('No results to export')
      return
    }
    const rows = [
      ['Property', 'Value'],
      ['Original Query', `"${query.replace(/"/g, '""')}"`],
      ['Optimized Query', `"${optimizedQuery.replace(/"/g, '""')}"`],
      ['Improvement', metrics.improvement],
      ['Confidence', metrics.confidence],
      ['Execution Time', metrics.executionTime],
      ['Rows Scanned', metrics.rowsScanned],
      ['Status', isRejected ? 'Rejected' : 'Optimized'],
      ['Timestamp', new Date().toISOString()]
    ]
    const csvContent = rows.map(e => e.join(",")).join("\n")
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `optimql-export-${Date.now()}.csv`
    a.click()
    toast.success('CSV Exported')
  }

  return (
    <div className="min-h-screen bg-[#080C14] text-zinc-50 selection:bg-violet-900/50 selection:text-white font-sans overflow-x-hidden relative">
      
      {/* Navbar */}
      <header className="sticky top-0 z-50 bg-[#080C14]/80 backdrop-blur-xl border-b border-white/5">
        <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-violet-600 via-cyan-400 to-transparent opacity-50"></div>
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-cyan-400">
              &lt;/&gt;OptimQL
            </span>
          </div>

          <div className="hidden md:flex items-center bg-white/5 rounded-full p-1 border border-white/10">
            <button 
              onClick={() => setActiveTab('analyzer')} 
              className={`px-4 py-1.5 text-sm rounded-full font-medium transition-colors ${activeTab === 'analyzer' ? 'bg-white/10 text-white shadow-sm' : 'text-zinc-400 hover:text-white'}`}
            >
              Analyzer
            </button>
            <button 
              onClick={() => setActiveTab('history')} 
              className={`px-4 py-1.5 text-sm rounded-full font-medium transition-colors ${activeTab === 'history' ? 'bg-white/10 text-white shadow-sm' : 'text-zinc-400 hover:text-white'}`}
            >
              History
            </button>
            <button 
              onClick={() => setActiveTab('docs')} 
              className={`px-4 py-1.5 text-sm rounded-full font-medium transition-colors ${activeTab === 'docs' ? 'bg-white/10 text-white shadow-sm' : 'text-zinc-400 hover:text-white'}`}
            >
              Docs
            </button>
          </div>

          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/DebangarajKaushik10/OptimQL" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-zinc-400 hover:text-white transition-colors"
              title="View on GitHub"
            >
              <Github className="h-5 w-5" />
            </a>
            
            <div className="h-4 w-px bg-white/10 hidden sm:block"></div>

            <div className="flex items-center gap-2">
              <button 
                onClick={exportToJSON}
                className="p-2 rounded-full hover:bg-white/5 text-zinc-400 hover:text-amber-400 transition-all"
                title="Export JSON"
              >
                <FileJson className="h-5 w-5" />
              </button>
              
              <button 
                onClick={exportToCSV}
                className="p-2 rounded-full hover:bg-white/5 text-zinc-400 hover:text-emerald-400 transition-all"
                title="Export CSV"
              >
                <FileSpreadsheet className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 relative z-10 min-h-[60vh]">
        <div className="max-w-5xl mx-auto space-y-12">
          
          {activeTab === 'analyzer' && (
            <div className="space-y-12">
              {/* Hero Content */}
              <div className="text-center space-y-6 pt-10 pb-4">
                <motion.h1 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-5xl md:text-6xl font-bold tracking-tight text-white mb-2 font-sans"
                >
                  Optimize SQL. <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-cyan-400">Instantly.</span>
                </motion.h1>
                <motion.p 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-lg text-zinc-400 max-w-2xl mx-auto"
                >
                  AI agents analyze execution structures, suggest indexes, and validate rewrite improvements in real-time.
                </motion.p>
              </div>

              {/* Editor Space */}
              <motion.div 
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="space-y-4"
              >
                <QueryEditor value={query} onChange={setQuery} />

                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pt-2">
                  <div className="flex flex-wrap gap-2">
                    {exampleQueries.map((ex, i) => (
                      <button 
                        key={i}
                        onClick={() => loadExample(ex.sql)}
                        className="px-3 py-1 text-xs font-mono rounded-full border border-white/10 bg-white/5 text-zinc-300 hover:border-violet-500/50 hover:text-violet-300 transition-colors"
                      >
                        {ex.label}
                      </button>
                    ))}
                  </div>
                  
                  <button 
                    onClick={optimizeQuery} 
                    disabled={isOptimizing}
                    className="relative group overflow-hidden rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-3 text-sm font-medium text-white shadow-[0_0_20px_rgba(124,58,237,0.4)] disabled:opacity-50 hover:shadow-[0_0_30px_rgba(124,58,237,0.6)] transition-all active:scale-95"
                  >
                    <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:animate-[shimmer_1.5s_infinite] skew-x-[-20deg]"></div>
                    <div className="relative flex items-center gap-2">
                      {isOptimizing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                      {isOptimizing ? 'Analyzing...' : 'Analyze'}
                    </div>
                  </button>
                </div>
              </motion.div>

              {/* Agent Visualizer */}
              <AnimatePresence>
                {(isOptimizing || hasResults) && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <AgentPipeline isOptimizing={isOptimizing} hasResults={hasResults} isRejected={isRejected} />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Results Panel */}
              <AnimatePresence>
                {hasResults && (
                  <motion.div
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ type: "spring", bounce: 0.3 }}
                    className="space-y-6 pt-4 border-t border-white/5"
                  >
                    <PerformanceMetrics metrics={metrics} />
                    <OptimizationResults originalQuery={query} optimizedQuery={optimizedQuery} suggestions={suggestions} />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Empty State */}
              {!hasResults && !isOptimizing && (
                <motion.div 
                   initial={{ opacity: 0 }}
                   animate={{ opacity: 1 }}
                   transition={{ delay: 0.5 }}
                   className="py-16 text-center opacity-40"
                >
                  <Terminal className="h-10 w-10 mx-auto text-zinc-600 mb-3" strokeWidth={1} />
                  <p className="font-mono text-sm text-zinc-500">Awaiting payload sequence...</p>
                </motion.div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
              className="space-y-6 pt-10 pb-4 text-center"
            >
              <h2 className="text-3xl font-bold tracking-tight text-white mb-2 font-sans">Optimization History</h2>
              
              {isLoadingHistory ? (
                <div className="py-16 text-center text-zinc-500">
                  <Loader2 className="h-8 w-8 mx-auto animate-spin mb-3 opacity-50 text-violet-500" />
                  <p className="font-mono text-sm">Fetching cached sequences...</p>
                </div>
              ) : historyLog.length === 0 ? (
                <div className="py-16 border border-white/5 rounded-[4px] bg-[#0F1623]/80 backdrop-blur-md">
                  <Terminal className="h-10 w-10 mx-auto text-zinc-600 mb-3" strokeWidth={1} />
                  <p className="font-mono text-sm text-zinc-500">No cached optimizations found in current session.</p>
                </div>
              ) : (
                <div className="space-y-4 max-w-4xl mx-auto text-left">
                  {historyLog.map((item, i) => (
                    <motion.div 
                      key={i} 
                      initial={{ opacity: 0, y: 10 }} 
                      animate={{ opacity: 1, y: 0 }} 
                      transition={{ delay: i * 0.05 }}
                      className="p-5 border border-white/5 bg-[#080C14] rounded-[4px] flex flex-col md:flex-row justify-between items-start md:items-center gap-6 group hover:border-violet-500/30 transition-colors shadow-lg"
                    >
                       <div className="flex-1">
                          <div className="text-xs text-zinc-500 font-mono mb-2 flex items-center gap-2">
                             <span>{new Date(item.timestamp).toLocaleString()}</span>
                             {item.improvement_pct > 0 && item.suggested_query && (
                                <span className="px-1.5 py-0.5 rounded-sm bg-emerald-500/10 text-emerald-400 text-[10px] uppercase">Optimized</span>
                             )}
                          </div>
                          <pre className="text-sm text-zinc-300 font-mono line-clamp-2 max-w-2xl bg-black/30 p-2 rounded border border-white/5">{item.original_query}</pre>
                       </div>
                       <div className="flex items-center gap-6 self-end md:self-auto shrink-0">
                          <div className="text-right">
                            <div className="text-xl text-emerald-400 font-mono font-bold">{item.improvement_pct ? item.improvement_pct.toFixed(0) : 0}%</div>
                            <div className="text-[10px] text-zinc-500 uppercase tracking-widest whitespace-nowrap">Scan Reduction</div>
                          </div>
                          <button 
                            onClick={() => { setQuery(item.original_query); setActiveTab('analyzer'); }}
                            className="px-4 py-2 text-xs font-semibold rounded-[4px] bg-white/5 hover:bg-violet-600 border border-white/10 hover:border-violet-500 text-white transition-all shadow-sm"
                          >
                            Load
                          </button>
                       </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'docs' && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
              className="space-y-8 pt-10 pb-4 max-w-3xl mx-auto"
            >
              <h2 className="text-3xl font-bold tracking-tight text-white mb-2 font-sans">Documentation</h2>
              <div className="p-8 border border-white/5 rounded-[4px] bg-[#0F1623]/80 backdrop-blur-md space-y-6 text-zinc-300">
                <div>
                  <h3 className="text-xl text-violet-400 font-semibold mb-2">Agent Pipeline</h3>
                  <p className="text-sm leading-relaxed">OptimQL utilizes a multi-step verification pipeline. Your query is passed through a Safety agent to strip mutations, an Analysis agent to construct a cost plan, and an Optimization agent to recommend B-Trees or rewrite logic. It is then statically validated.</p>
                </div>
                <div className="h-px bg-white/5 w-full"></div>
                <div>
                  <h3 className="text-xl text-cyan-400 font-semibold mb-2">Confidence Scores</h3>
                  <p className="text-sm leading-relaxed">The confidence gauge represents the mathematical difference in structural execution cost. A score of {'<50%'} acts strictly as a suggestion to investigate missing foreign keys.</p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </main>

    </div>
  )
}
