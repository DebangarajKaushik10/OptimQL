import React from 'react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline'
  className?: string
  children?: React.ReactNode
  onClick?: React.MouseEventHandler<HTMLButtonElement>
  disabled?: boolean
}

export function Button({ variant = 'default', className = '', children, ...rest }: ButtonProps) {
  const base = 'px-4 py-2 text-sm'
  const style = variant === 'outline' ? 'border border-zinc-800 text-zinc-100' : 'bg-zinc-100 text-black'
  return (
    <button className={`${base} ${style} ${className}`} {...rest}>
      {children}
    </button>
  )
}

export default Button
