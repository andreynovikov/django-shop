// Tailwind classes of Cartzilla's form controls and the texts around them

const controlSizes = {
  sm: 'rounded-sm px-3 py-[.425rem] text-ms',
  md: 'rounded-md px-4 py-2.5 text-md',
  lg: 'rounded-lg px-5 py-3 text-[1.0625rem]',
}

const control = 'border bg-white leading-normal text-body transition-[border-color,box-shadow] duration-150 placeholder:text-gray-500 focus:outline-none disabled:bg-gray-200'

function stateClass(invalid: boolean) {
  return invalid
    ? 'border-danger focus:shadow-[0_.375rem_.625rem_-.3125rem_rgb(204_29_29/.15)]'
    : 'border-gray-400 focus:border-[#f7bf8d] focus:shadow-[0_.375rem_.625rem_-.3125rem_rgb(239_127_26/.15)]'
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

// A select with Cartzilla's chevron
export function selectClass({ size = 'md', invalid = false, full = true }: ControlOptions = {}) {
  return `${full ? 'block w-full' : 'inline-block'} ${control} ${controlSizes[size]} ${stateClass(invalid)} appearance-none bg-[url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2016%2016'%3e%3cpath%20fill='none'%20stroke='%23373f50'%20stroke-linecap='round'%20stroke-linejoin='round'%20stroke-width='2'%20d='M2%205l6%206%206-6'/%3e%3c/svg%3e")] bg-size-[15px_11px] bg-position-[right_1rem_center] bg-no-repeat pe-10`
}

// An input group: controls and buttons in a row, the inner corners square
export const inputGroupClass = 'relative flex w-full flex-wrap items-stretch'
// A control inside an input group takes the remaining width
export const groupedInputClass = 'relative min-w-0 flex-1 focus:z-3'

// A label above its input
export const labelClass = 'mb-1.5 inline-block text-sm font-medium text-heading'

// A hint below the input
export const formTextClass = 'mt-1.5 block text-xs text-muted'

// An error below the input, rendered only when there is one
export const feedbackClass = 'mt-1.5 w-full text-xs text-danger'

// A checkbox or radio before its label, the label lines are aligned when wrapped; `inline` ones stand in a row
export function checkClass({ inline = false }: { inline?: boolean } = {}) {
  return `min-h-6 ps-[1.5em] ${inline ? 'me-4 inline-block' : 'block'}`
}

export const checkLabelClass = 'text-sm'

export function checkInputClass({ invalid = false }: { invalid?: boolean } = {}) {
  return `float-left -ms-[1.5em] mt-[.25em] size-[1em] accent-primary ${invalid ? 'outline outline-offset-1 outline-danger' : ''}`
}
