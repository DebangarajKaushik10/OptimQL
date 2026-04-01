import React, { useState } from 'react'
import { Code2 } from 'lucide-react'
import Textarea from './ui/textarea'

interface QueryEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function QueryEditor({ value, onChange, placeholder }: QueryEditorProps) {
  const [isFocused, setIsFocused] = useState(false)
  const lineCount = value ? value.split('\n').length : 1
  const charCount = value.length

  return (
    <div className="space-y-3">
      <div className={`relative transition-all duration-300 rounded-lg overflow-hidden bg-[#0F1623] border border-white/5 shadow-2xl backdrop-blur-md ${isFocused ? 'ring-1 ring-violet-500/50 shadow-[0_0_30px_rgba(124,58,237,0.15)]' : ''}`}>
        
        {/* Fake macOS Title Bar */}
        <div className="h-10 bg-black/40 border-b border-white/5 flex items-center px-4 justify-between select-none">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-rose-500/80 border border-black/20"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/80 border border-black/20"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/80 border border-black/20"></div>
          </div>
          <div className="text-xs font-mono text-zinc-500">query.sql</div>
          <div className="w-11"></div> {/* Spacer for symmetry */}
        </div>

        {/* Editor Body */}
        <div className="relative flex">
          {/* Glowing Violet Left Border */}
          <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-gradient-to-b from-violet-500 to-cyan-500 opacity-50 z-10"></div>
          
          <div className="w-12 bg-black/20 flex flex-col items-end pr-3 py-4 text-xs text-zinc-600 font-mono select-none pointer-events-none shrink-0 border-r border-white/5">
            {Array.from({ length: Math.max(lineCount, 10) }, (_, i) => (
              <div key={i} className="leading-6">
                {i + 1}
              </div>
            ))}
          </div>

          <Textarea
            value={value}
            onChange={(e) => onChange((e.target as HTMLTextAreaElement).value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder || "-- SELECT u.name, o.total FROM users u JOIN orders o ON o.user_id = u.id WHERE o.status = 'pending'"}
            className="w-full font-mono text-sm min-h-[240px] resize-none bg-transparent text-zinc-100 border-none focus:ring-0 rounded-none placeholder:text-zinc-600/50 px-4 py-4 transition-all duration-300"
            style={{ lineHeight: '1.5rem', outline: 'none' }}
          />
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-violet-500/20 to-transparent object-cover"></div>
      </div>
      
      {/* Bottom Row Details */}
      {value && (
        <div className="flex items-center justify-between px-1">
          <div className="flex gap-2 items-center">
            <span className="text-xs text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded-full font-mono border border-cyan-400/20">
              {value.trim().toUpperCase().startsWith('SELECT') ? 'SELECT' : value.trim().toUpperCase().startsWith('UPDATE') ? 'UPDATE' : value.trim().toUpperCase().startsWith('DELETE') ? 'DELETE' : value.trim().toUpperCase().startsWith('INSERT') ? 'INSERT' : 'QUERY'}
            </span>
          </div>
          <div className="text-xs text-zinc-600 font-mono">
            {lineCount} lines · {charCount} chars
          </div>
        </div>
      )}
    </div>
  )
}

export default QueryEditor
