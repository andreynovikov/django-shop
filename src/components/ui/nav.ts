// Tailwind classes of Cartzilla's navigation links

// A gray link that turns primary on hover or when active (Cartzilla's .nav-link-style)
export function navLinkClass({ active = false, light = false }: { active?: boolean, light?: boolean } = {}) {
  if (light)
    return `transition-colors ${active ? 'text-white' : 'text-white/65 hover:text-white'}`
  return `transition-colors ${active ? 'text-primary' : 'text-gray-700 hover:text-primary'}`
}
