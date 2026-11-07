import { ReactNode } from 'react'

// Cartzilla's alert colors: text, background, border and the icon box's tint
const variants = {
  success: { box: 'border-[#c6e6c6] bg-[#eff8ef] text-[#53a653]', icon: 'bg-success/10' },
  danger: { box: 'border-[#edb0b0] bg-[#fae8e8] text-[#b81a1a]', icon: 'bg-danger/10' },
  info: { box: 'border-[#c6daf3] bg-[#eff5fc] text-[#5287c8]', icon: 'bg-info/10' },
  accent: { box: 'border-[#b7c8e2] bg-[#eaeff7] text-[#2c599c]', icon: 'bg-accent/10' },
  warning: { box: 'border-[#fae2c1] bg-[#fef7ed] text-[#d89c46]', icon: 'bg-warning/10' },
  secondary: { box: 'border-gray-300 bg-gray-100 text-gray-700', icon: 'bg-gray-300' },
}

// A message box, with an icon its text goes next to a tinted strip at the left edge.
// Its links are underlined in the text color.
export function Alert({ variant, icon, className = '', children }: {
  variant: keyof typeof variants,
  icon?: ReactNode,
  className?: string,
  children: ReactNode
}) {
  const { box, icon: iconBox } = variants[variant]
  return (
    <div className={`rounded-lg border px-[1.125rem] py-3 [&_a]:text-current [&_a]:underline [&_a]:hover:no-underline ${icon ? 'flex' : ''} ${box} ${className}`} role="alert">
      {icon && (
        <div className={`-my-3 me-[1.125rem] -ms-[1.125rem] flex items-center rounded-s-lg p-[.75em] text-lg ${iconBox}`}>
          {icon}
        </div>
      )}
      <div>{children}</div>
    </div>
  )
}
