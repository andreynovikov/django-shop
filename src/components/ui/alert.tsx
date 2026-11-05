import { ReactNode } from 'react'

const variants = {
  success: 'border-green-200 bg-green-50 text-green-800',
  info: 'border-sky-200 bg-sky-50 text-sky-800',
  accent: 'border-orange-200 bg-orange-50 text-orange-900',
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
