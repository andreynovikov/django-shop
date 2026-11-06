// Tailwind classes of a button, also for a link or a span that looks like one, sized as Bootstrap's .btn.
// Classes added next to these must not set what they set: display, padding, font size, border and colors.

const base = 'items-center justify-center border text-center align-middle leading-normal no-underline select-none transition-colors hover:no-underline focus-visible:outline-none focus-visible:ring-4 disabled:pointer-events-none disabled:opacity-65'

const variants = {
  'primary': 'border-primary bg-primary text-white hover:border-primary-hover hover:bg-primary-hover focus-visible:ring-primary/50',
  'outline-primary': 'border-primary text-primary hover:bg-primary hover:text-white focus-visible:ring-primary/50',
  'success': 'border-success bg-success text-white hover:border-success-hover hover:bg-success-hover focus-visible:ring-success/50',
  'outline-success': 'border-success text-success hover:bg-success hover:text-white focus-visible:ring-success/50',
}

const sizes = {
  icon: 'rounded px-1 py-0 text-sm', // a small button with an icon only
  sm: 'rounded px-2 py-1 text-sm',
  md: 'rounded-md px-3 py-1.5',
  lg: 'rounded-lg px-4 py-2 text-lg',
}

export type ButtonVariant = keyof typeof variants
export type ButtonSize = keyof typeof sizes

// A block button takes the full width
export function buttonClass({ variant = 'primary', size = 'md', block = false }: {
  variant?: ButtonVariant,
  size?: ButtonSize,
  block?: boolean
} = {}) {
  return `${block ? 'flex w-full' : 'inline-flex'} ${base} ${variants[variant]} ${sizes[size]}`
}
