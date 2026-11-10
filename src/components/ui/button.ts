// Tailwind classes of a button, also for a link or a span that looks like one: Singer's look with the API of cartzilla's.
// Classes added next to these must not set what they set: display, padding, font size, border and colors.

const base = 'items-center border align-middle leading-tight no-underline select-none transition-colors hover:no-underline focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/25 disabled:pointer-events-none disabled:opacity-65'

const variants = {
  'primary': 'border-primary bg-primary text-white hover:border-primary-hover hover:bg-primary-hover',
  'outline-primary': 'border-primary text-primary hover:bg-primary hover:text-white',
  'warning': 'border-warning bg-warning text-white hover:border-warning-hover hover:bg-warning-hover',
  'success': 'border-success bg-success text-white hover:border-success-hover hover:bg-success-hover',
  'outline-success': 'border-success text-success hover:bg-success hover:text-white',
  'link': 'border-transparent text-primary hover:text-primary-hover',
  'link-danger': 'border-transparent text-danger hover:underline',
  'wb': 'border-wb bg-wb text-white hover:border-wb-hover hover:bg-wb-hover',
  'ozon': 'border-ozon bg-ozon text-white hover:border-ozon-hover hover:bg-ozon-hover',
}

const sizes = {
  xs: 'rounded px-2 py-1 text-2xs',
  sm: 'rounded px-2 py-1 text-xs',
  md: 'rounded-md px-3 py-1.5',
  lg: 'rounded-lg px-4 py-2 text-lg',
  'icon-sm': 'rounded px-1 py-0 text-xs', // a small button with an icon only, in a table row
  flush: 'rounded-md px-0 py-1.5', // a link button without side padding
}

export type ButtonVariant = keyof typeof variants
export type ButtonSize = keyof typeof sizes

// A block button takes the full width; `start` puts its content at the start instead of the middle.
// `shadow` is cartzilla's glow, Singer's buttons have none.
export function buttonClass({ variant = 'primary', size = 'md', block = false, start = false }: {
  variant?: ButtonVariant,
  size?: ButtonSize,
  block?: boolean,
  shadow?: boolean,
  start?: boolean,
} = {}) {
  return `${block ? 'flex w-full' : 'inline-flex'} ${start ? 'justify-start text-start' : 'justify-center text-center'} ${base} ${variants[variant]} ${sizes[size]}`
}
