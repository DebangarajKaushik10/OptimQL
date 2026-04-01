import React from 'react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline'
  className?: string
  children?: React.ReactNode
  onClick?: React.MouseEventHandler<HTMLButtonElement>
  disabled?: boolean
}

export function Button({ variant = 'default', className = '', children, ...rest }: ButtonProps) {
  const base = 'inline-flex items-center justify-center px-4 py-2 text-sm rounded-md font-medium transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none'
  const style = variant === 'outline' 
    ? 'border border-zinc-800 text-zinc-300 hover:text-zinc-50 hover:bg-zinc-900' 
    : 'bg-zinc-100 text-zinc-950 hover:bg-white shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]'
  return (
    <button className={`${base} ${style} ${className}`} {...rest}>
      {children}
    </button>
  )
}

export default Button
