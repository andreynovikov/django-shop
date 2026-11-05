// Tailwind classes of a button, also for a link that looks like one: square, bold, uppercase and widely spaced.
// Classes added next to these must not set what they set: display, padding, height, font size, border and colors.

const base = 'items-center justify-center border text-center align-middle font-bold leading-normal tracking-[.3em] uppercase no-underline select-none transition-colors hover:no-underline focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-dark/25 disabled:pointer-events-none disabled:opacity-65'

const variants = {
  'dark': 'border-dark bg-dark text-white hover:border-dark-hover hover:bg-dark-hover hover:text-white',
  'secondary': 'border-secondary bg-secondary text-white hover:border-secondary-hover hover:bg-secondary-hover hover:text-white',
  'outline-secondary': 'border-secondary text-secondary hover:bg-secondary hover:text-white',
  'link-danger': 'border-transparent text-danger', // a button without a frame, e.g. to remove an item
}

const sizes = {
  sm: 'px-2 py-1 text-2xs',
  md: 'px-3 py-[.7rem] text-2xs',
  lg: 'p-6 text-xs',
  overlay: 'h-10 px-8 text-2xs', // over the product image in a card
}

export type ButtonVariant = keyof typeof variants
export type ButtonSize = keyof typeof sizes

// A block button takes the full width
export function buttonClass({ variant = 'dark', size = 'md', block = false }: {
  variant?: ButtonVariant,
  size?: ButtonSize,
  block?: boolean
} = {}) {
  return `${block ? 'flex w-full' : 'inline-flex'} ${base} ${variants[variant]} ${sizes[size]}`
}
