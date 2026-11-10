import { ReactNode } from 'react'

// Singer's message boxes, with the variants of cartzilla's
const variants = {
  success: 'border-green-200 bg-green-50 text-green-800',
  info: 'border-sky-200 bg-sky-50 text-sky-800',
  accent: 'border-orange-200 bg-orange-50 text-orange-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  danger: 'border-red-200 bg-red-50 text-red-800',
  secondary: 'border-stone-200 bg-stone-50 text-stone-700',
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
