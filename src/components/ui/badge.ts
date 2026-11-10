// Tailwind classes of a badge, its colors are added next to them; a pill has round ends.
// Its text is smaller than the text around it, `sm` sets it to text-sm.
export function badgeClass({ pill = false, size }: { pill?: boolean, size?: 'sm' } = {}) {
  return `inline-block px-2 py-1 text-center align-baseline font-bold leading-none whitespace-nowrap ${size === 'sm' ? 'text-sm' : 'text-[.75em]'} ${pill ? 'rounded-full' : 'rounded-md'}`
}
