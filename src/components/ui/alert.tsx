import { ReactNode } from 'react'

// Cartzilla's alert colors, as Bootstrap derives them from a theme color: the background and the border are the color
// tinted 90% and 65%, the text is the color shaded 10%
const tinted = 'border-[color-mix(in_srgb,var(--alert-color)_35%,white)] bg-[color-mix(in_srgb,var(--alert-color)_10%,white)] text-[color-mix(in_srgb,var(--alert-color)_90%,black)]'

// Text, background, border and the icon box's tint
const variants = {
  success: { box: `${tinted} [--alert-color:var(--color-success)]`, icon: 'bg-success/10' },
  danger: { box: `${tinted} [--alert-color:var(--color-danger)]`, icon: 'bg-danger/10' },
  info: { box: `${tinted} [--alert-color:var(--color-info)]`, icon: 'bg-info/10' },
  accent: { box: `${tinted} [--alert-color:var(--color-accent)]`, icon: 'bg-accent/10' },
  warning: { box: `${tinted} [--alert-color:var(--color-warning)]`, icon: 'bg-warning/10' },
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
