// Tailwind classes of navigation links, such as the account menu: Singer's links with the API of cartzilla's

export function navLinkClass({ active = false }: { active?: boolean, light?: boolean } = {}) {
  return `transition-colors hover:no-underline ${active ? 'text-primary-hover' : 'text-primary hover:text-primary-hover'}`
}
