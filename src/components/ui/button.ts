// Tailwind classes of a button, also for a link or a span that looks like one: Dor Tak's look with the API of cartzilla's.
// Classes added next to these must not set what they set: display, padding, font size, border and colors.

const base = 'items-center border align-middle leading-normal no-underline select-none transition-colors hover:no-underline focus-visible:outline-none focus-visible:ring-4 disabled:pointer-events-none disabled:opacity-65'

const variants = {
  'primary': 'border-primary bg-primary text-white hover:border-primary-hover hover:bg-primary-hover focus-visible:ring-primary/50',
  'outline-primary': 'border-primary text-primary hover:bg-primary hover:text-white focus-visible:ring-primary/50',
  'success': 'border-success bg-success text-white hover:border-success-hover hover:bg-success-hover focus-visible:ring-success/50',
  'outline-success': 'border-success text-success hover:bg-success hover:text-white focus-visible:ring-success/50',
  'link': 'border-transparent text-primary underline hover:text-primary-hover focus-visible:ring-primary/50',
  'link-danger': 'border-transparent text-danger underline hover:no-underline focus-visible:ring-danger/50',
}

const sizes = {
  sm: 'rounded px-2 py-1 text-sm',
  md: 'rounded-md px-3 py-1.5',
  lg: 'rounded-lg px-4 py-2 text-lg',
  'icon-sm': 'rounded px-1 py-0 text-sm', // a small button with an icon only, in a table row
  flush: 'rounded-md px-0 py-1.5', // a link button without side padding
}

export type ButtonVariant = keyof typeof variants
export type ButtonSize = keyof typeof sizes

// A block button takes the full width; `start` puts its content at the start instead of the middle.
// `shadow` is cartzilla's glow, Dor Tak's buttons have none.
export function buttonClass({ variant = 'primary', size = 'md', block = false, start = false }: {
  variant?: ButtonVariant,
  size?: ButtonSize,
  block?: boolean,
  shadow?: boolean,
  start?: boolean,
} = {}) {
  return `${block ? 'flex w-full' : 'inline-flex'} ${start ? 'justify-start text-start' : 'justify-center text-center'} ${base} ${variants[variant]} ${sizes[size]}`
}
