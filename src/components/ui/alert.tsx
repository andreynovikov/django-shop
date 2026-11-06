import { ReactNode } from 'react'

// The accent is the success color
const variants = {
  success: 'border-success-border bg-success-subtle text-success-emphasis',
  info: 'border-info-border bg-info-subtle text-info-emphasis',
  accent: 'border-success-border bg-success-subtle text-success-emphasis',
}

// A message box with an icon before the text. Its links are `font-bold text-inherit`.
export function Alert({ variant, icon, className = '', children }: {
  variant: keyof typeof variants,
  icon: ReactNode,
  className?: string,
  children: ReactNode
}) {
  return (
    <div className={`mb-4 flex items-center gap-4 rounded-md border p-4 ${variants[variant]} ${className}`} role="alert">
      {icon}
      <div>{children}</div>
    </div>
  )
}
