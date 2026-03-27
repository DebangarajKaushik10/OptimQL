import React from 'react'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  className?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
  onFocus?: (e: React.FocusEvent<HTMLTextAreaElement>) => void
  onBlur?: (e: React.FocusEvent<HTMLTextAreaElement>) => void
  placeholder?: string
  style?: React.CSSProperties
}

export const Textarea = ({ className = '', ...rest }: TextareaProps) => {
  return <textarea className={`w-full p-4 bg-black border border-zinc-800 ${className}`} {...rest} />
}

export default Textarea
