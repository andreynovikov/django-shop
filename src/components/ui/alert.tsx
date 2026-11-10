import { ReactNode } from 'react'

// Dor Tak's message boxes, with the variants of cartzilla's
const variants = {
  success: 'border-success-border bg-success-subtle text-success-emphasis',
  info: 'border-info-border bg-info-subtle text-info-emphasis',
  accent: 'border-success-border bg-success-subtle text-success-emphasis', // the accent is the success color
  warning: 'border-[#ffe69c] bg-[#fff3cd] text-[#664d03]',
  danger: 'border-[#f1aeb5] bg-[#f8d7da] text-[#58151c]',
  secondary: 'border-[#c4c8cb] bg-[#e2e3e5] text-[#2b2f32]',
}

// A message box, with an icon before the text. It has no margins, the caller sets them.
export function Alert({ variant, icon, className = '', children }: {
  variant: keyof typeof variants,
  icon?: ReactNode,
  className?: string,
  children: ReactNode
}) {
  return (
    <div className={`flex items-center gap-4 rounded-md border p-4 ${variants[variant]} ${className}`} role="alert">
      {icon && <span className="flex shrink-0">{icon}</span>}
      <div>{children}</div>
    </div>
  )
}
