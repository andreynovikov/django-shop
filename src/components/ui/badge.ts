// Tailwind classes of a badge, its colors are added next to them; a pill has round ends.
// Its text is smaller than the text around it, `sm` sets it to text-sm.
export function badgeClass({ pill = false, size }: { pill?: boolean, size?: 'sm' } = {}) {
  return `inline-block px-[.625em] py-[.25em] text-center align-baseline leading-none font-normal whitespace-nowrap ${size === 'sm' ? 'text-sm' : 'text-[.75em]'} ${pill ? 'rounded-full' : 'rounded-[.175rem]'}`
}

// Cartzilla's .badge-shadow: a glow in the badge's color, the colors follow the theme
export const badgeShadows = {
  primary: 'shadow-[0_.5rem_1.125rem_-.275rem_--alpha(var(--color-primary)/90%)]',
  accent: 'shadow-[0_.5rem_1.125rem_-.275rem_--alpha(var(--color-accent)/90%)]',
  success: 'shadow-[0_.5rem_1.125rem_-.275rem_--alpha(var(--color-success)/90%)]',
  danger: 'shadow-[0_.5rem_1.125rem_-.275rem_--alpha(var(--color-danger)/90%)]',
  info: 'shadow-[0_.5rem_1.125rem_-.275rem_--alpha(var(--color-info)/90%)]',
  warning: 'shadow-[0_.5rem_1.125rem_-.275rem_--alpha(var(--color-warning)/90%)]',
}
