// Tailwind classes of form controls and the texts around them

const inputSizes = {
  sm: 'rounded px-2 py-1 text-xs',
  md: 'rounded-md px-3 py-1.5',
  lg: 'rounded-lg px-4 py-2 text-lg',
}

// A text input, textarea or select taking the full width, its border is red when the value is invalid
export function inputClass({ size = 'md', invalid = false }: { size?: keyof typeof inputSizes, invalid?: boolean } = {}) {
  return `block w-full border bg-white leading-tight text-body placeholder:text-muted focus:outline-none focus:ring-4 disabled:bg-light ${inputSizes[size]} ${invalid ? 'border-danger focus:ring-danger/25' : 'focus:border-primary/50 focus:ring-primary/25'}`
}

// A label above its input
export const labelClass = 'mb-2 inline-block'

// A hint below the input
export const formTextClass = 'mt-1 block text-xs text-muted'

// An error below the input, rendered only when there is one
export const feedbackClass = 'mt-1 text-xs text-danger'

// A checkbox before its label, the label lines are aligned when wrapped
export const checkClass = 'ps-6'

export function checkInputClass({ invalid = false }: { invalid?: boolean } = {}) {
  return `float-start -ms-6 mt-px size-4 accent-primary ${invalid ? 'outline outline-offset-1 outline-danger' : ''}`
}
