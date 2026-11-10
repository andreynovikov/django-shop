// Tailwind classes of form controls and the texts around them: Singer's look with the API of cartzilla's,
// so the components that every storefront shares work unchanged

const controlSizes = {
  sm: 'rounded px-2 py-1 text-xs',
  md: 'rounded-md px-3 py-1.5',
  lg: 'rounded-lg px-4 py-2 text-lg',
}

const control = 'border bg-white leading-tight text-body placeholder:text-muted focus:outline-none focus:ring-4 disabled:bg-light'

function stateClass(invalid: boolean) {
  return invalid ? 'border-danger focus:ring-danger/25' : 'focus:border-primary/50 focus:ring-primary/25'
}

type ControlOptions = {
  size?: keyof typeof controlSizes,
  invalid?: boolean,
  full?: boolean,  // as wide as its container, otherwise the caller sets the width
}

// A text input or textarea, its border is red when the value is invalid
export function inputClass({ size = 'md', invalid = false, full = true }: ControlOptions = {}) {
  return `${full ? 'block w-full' : 'inline-block'} ${control} ${controlSizes[size]} ${stateClass(invalid)}`
}

// A select, with the browser's arrow
export function selectClass(options: ControlOptions = {}) {
  return inputClass(options)
}

// A label above its input
export const labelClass = 'mb-2 inline-block'

// A hint below the input
export const formTextClass = 'mt-1 block text-xs text-muted'

// An error below the input, rendered only when there is one
export const feedbackClass = 'mt-1 w-full text-xs text-danger'

// A checkbox or radio before its label, the label lines are aligned when wrapped; `inline` ones stand in a row
export function checkClass({ inline = false }: { inline?: boolean } = {}) {
  return `ps-6 ${inline ? 'me-4 inline-block' : 'block'}`
}

// The label of a checkbox keeps the size of the text around it
export const checkLabelClass = ''

export function checkInputClass({ invalid = false }: { invalid?: boolean } = {}) {
  return `float-start -ms-6 mt-px size-4 accent-primary ${invalid ? 'outline outline-offset-1 outline-danger' : ''}`
}
