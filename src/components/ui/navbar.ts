// Tailwind classes of Cartzilla's header tools: an icon in a circle with an optional counter, and two lines of text
// next to it from lg up. A tool is a `group`, so its parts change color together on hover.

// It sets no display, callers add flex or e.g. hidden lg:flex
export const navbarToolClass = 'group relative items-center'

export function navbarToolIconClass({ secondary = false }: { secondary?: boolean } = {}) {
  return `relative flex size-[2.875rem] shrink-0 items-center justify-center rounded-full text-gray-700 transition-colors group-hover:text-gray-900 ${secondary ? 'bg-secondary' : ''}`
}

// The counter at the icon's top right
export const navbarToolLabelClass = 'absolute -top-[.3125rem] -right-[.3125rem] size-5 rounded-full bg-primary text-center text-xs leading-5 font-medium text-white'

// The text; `dropdown` adds a caret after it
export function navbarToolTextClass({ dropdown = false }: { dropdown?: boolean } = {}) {
  return `hidden shrink-0 grow-0 ps-3.5 text-sm whitespace-nowrap text-gray-700 transition-colors group-hover:text-gray-900 lg:block ${dropdown ? caretClass : ''}`
}

// The first line of the text, small and muted
export const navbarToolCaptionClass = '-mb-0.5 block text-muted'

// Bootstrap's .dropdown-toggle caret, a small triangle after the text
export const caretClass = 'after:ms-[.23375rem] after:inline-block after:border-x-[.275rem] after:border-t-[.275rem] after:border-b-0 after:border-x-transparent after:border-t-current after:align-[.23375rem]'
