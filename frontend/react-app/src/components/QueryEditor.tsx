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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <Code2 className="h-4 w-4" />
          <span>Input Query</span>
        </div>
        {value && (
          <div className="text-xs text-zinc-600 font-mono">
            {lineCount} lines · {charCount} chars
          </div>
        )}
      </div>

      <div className={`relative transition-all duration-300 ${isFocused ? 'ring-1 ring-zinc-700' : ''}`}>
        <div className="absolute left-0 top-0 bottom-0 w-12 bg-zinc-950 border-r border-zinc-800 flex flex-col items-end pr-3 py-4 text-xs text-zinc-700 font-mono select-none pointer-events-none">
          {Array.from({ length: Math.max(lineCount, 10) }, (_, i) => (
            <div key={i} className="leading-6">
              {i + 1}
            </div>
          ))}
        </div>

        <div className={`absolute -top-px -right-px w-8 h-8 transition-opacity duration-500 ${isFocused ? 'opacity-100' : 'opacity-0'}`}>
          <div className="absolute top-0 right-0 w-8 h-8 bg-zinc-100 blur-xl opacity-20"></div>
          <div className="absolute top-0 right-0 w-4 h-px bg-zinc-400"></div>
          <div className="absolute top-0 right-0 w-px h-4 bg-zinc-400"></div>
        </div>

        <Textarea
          value={value}
          onChange={(e) => onChange((e.target as HTMLTextAreaElement).value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder || 'SELECT * FROM users WHERE ...'}
          className="font-mono text-sm min-h-[240px] resize-none bg-black text-zinc-100 border-zinc-800 focus:border-zinc-700 rounded-none placeholder:text-zinc-600 pl-16 transition-all duration-300"
          style={{ lineHeight: '1.5rem' }}
        />

        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-zinc-700 to-transparent opacity-50"></div>
      </div>
    </div>
  )
}

export default QueryEditor
