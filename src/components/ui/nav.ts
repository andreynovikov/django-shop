// Tailwind classes of navigation links, such as the account menu: Dor Tak's links with the API of cartzilla's

export function navLinkClass({ active = false }: { active?: boolean, light?: boolean } = {}) {
  return `no-underline transition-colors ${active ? 'text-primary-hover' : 'text-primary hover:text-primary-hover'}`
}
