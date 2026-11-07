// Tailwind classes of a badge, its colors are added next to them; a pill has round ends.
// Its text is smaller than the text around it, `sm` sets it to text-sm.
export function badgeClass({ pill = false, size }: { pill?: boolean, size?: 'sm' } = {}) {
  return `inline-block px-[.625em] py-[.25em] text-center align-baseline leading-none font-normal whitespace-nowrap ${size === 'sm' ? 'text-sm' : 'text-[.75em]'} ${pill ? 'rounded-full' : 'rounded-[.175rem]'}`
}

// Cartzilla's .badge-shadow: a glow in the badge's color
export const badgeShadows = {
  primary: 'shadow-[0_.5rem_1.125rem_-.275rem_rgb(239_127_26/.9)]',
  accent: 'shadow-[0_.5rem_1.125rem_-.275rem_rgb(49_99_173/.9)]',
  success: 'shadow-[0_.5rem_1.125rem_-.275rem_rgb(92_184_92/.9)]',
  danger: 'shadow-[0_.5rem_1.125rem_-.275rem_rgb(204_29_29/.9)]',
  info: 'shadow-[0_.5rem_1.125rem_-.275rem_rgb(91_150_222/.9)]',
  warning: 'shadow-[0_.5rem_1.125rem_-.275rem_rgb(240_173_78/.9)]',
}
