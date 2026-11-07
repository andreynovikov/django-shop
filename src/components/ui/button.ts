// Tailwind classes of Cartzilla's buttons, also for a link or a span that looks like one.
// Classes added next to these must not set what they set: display, padding, font size, border, colors and shadow.

const base = 'items-center border align-middle leading-normal whitespace-nowrap no-underline select-none transition-[color,background-color,border-color,box-shadow] duration-200 hover:no-underline focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-primary/25 disabled:pointer-events-none disabled:opacity-65'

const variants = {
  'primary': 'border-primary bg-primary text-white hover:border-primary-hover hover:bg-primary-hover hover:text-white',
  'accent': 'border-accent bg-accent text-white hover:border-accent-hover hover:bg-accent-hover hover:text-white',
  'success': 'border-success bg-success text-white hover:border-success-hover hover:bg-success-hover hover:text-white',
  'info': 'border-info bg-info text-white hover:border-info-hover hover:bg-info-hover hover:text-white',
  'dark': 'border-dark bg-dark text-white hover:border-dark-hover hover:bg-dark-hover hover:text-white',
  'secondary': 'border-gray-300 bg-secondary text-gray-700 hover:border-secondary-hover hover:bg-secondary-hover hover:text-gray-700',
  'light': 'border-transparent bg-white text-gray-700 hover:text-gray-700',
  'outline-primary': 'border-primary/35 text-primary hover:border-primary hover:bg-primary hover:text-white',
  'outline-secondary': 'border-gray-400 text-gray-700 hover:bg-secondary hover:text-gray-700',
  'outline-success': 'border-success/35 text-success hover:border-success hover:bg-success hover:text-white',
  'outline-danger': 'border-danger/35 text-danger hover:border-danger hover:bg-danger hover:text-white',
  'link': 'border-transparent text-primary hover:text-link-hover',
  'link-danger': 'border-transparent text-danger hover:text-danger/80',
}

// Cartzilla's .btn-shadow: a glow in the button's color, gone on hover
const shadows: Partial<Record<ButtonVariant, string>> = {
  'primary': 'shadow-[0_.5rem_1.125rem_-.5rem_rgb(239_127_26/.9)] hover:shadow-none',
  'accent': 'shadow-[0_.5rem_1.125rem_-.5rem_rgb(49_99_173/.9)] hover:shadow-none',
  'success': 'shadow-[0_.5rem_1.125rem_-.5rem_rgb(92_184_92/.9)] hover:shadow-none',
  'secondary': 'shadow-[0_.5rem_1.125rem_-.5rem_rgb(243_245_249/.9)] hover:shadow-none',
}

const sizes = {
  sm: 'rounded-sm px-4 py-[.425rem] text-ms',
  md: 'rounded-md px-[1.375rem] py-2.5 text-md',
  wide: 'rounded-md px-12 py-2.5 text-md', // a short label, e.g. - and + of a quantity
  lg: 'rounded-lg px-6 py-3 text-[1.0625rem]',
  icon: 'rounded-md p-2.5 text-md', // a square button with an icon only
  'icon-sm': 'rounded-sm px-1 py-0 text-ms', // a small one in a table row
  flush: 'rounded-md px-0 py-2.5 text-md', // a link button without side padding
}

export type ButtonVariant = keyof typeof variants
export type ButtonSize = keyof typeof sizes

// A block button takes the full width; `start` puts its content at the start instead of the middle
export function buttonClass({ variant = 'primary', size = 'md', block = false, shadow = false, start = false }: {
  variant?: ButtonVariant,
  size?: ButtonSize,
  block?: boolean,
  shadow?: boolean,
  start?: boolean,
} = {}) {
  return `${block ? 'flex w-full' : 'inline-flex'} ${start ? 'justify-start text-start' : 'justify-center text-center'} ${base} ${variants[variant]} ${sizes[size]} ${shadow ? shadows[variant] ?? '' : ''}`
}
