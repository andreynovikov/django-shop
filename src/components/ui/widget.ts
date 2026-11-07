// Tailwind classes of Cartzilla's widgets: titled lists of links in sidebars, menus and the footer

export const widgetTitleClass = 'mb-[1.125rem] text-[1.0625rem] leading-[1.2] font-medium text-heading'

export const widgetListItemClass = 'mb-2 last:mb-0'

// A link of a widget list, gray and primary on hover; `light` for dark backgrounds
export function widgetLinkClass({ light = false, active = false }: { light?: boolean, active?: boolean } = {}) {
  if (light)
    return 'block text-sm text-white/65 transition-colors hover:text-white'
  return `block text-sm transition-colors ${active ? 'text-primary' : 'text-gray-700 hover:text-primary'}`
}

// Product titles and details in the cart and order widgets
export const widgetProductTitleClass = 'text-sm font-medium [&_a]:text-heading [&_a]:hover:text-primary'
export const widgetProductMetaClass = 'text-sm'

// A tag link (Cartzilla's .btn-tag)
export function tagClass({ active = false }: { active?: boolean } = {}) {
  return `inline-block rounded-sm border px-[.5625rem] py-1.5 text-xs whitespace-nowrap transition-colors ${active
    ? 'border-primary bg-primary text-white shadow-[0_.5rem_1.125rem_-.5rem_rgb(239_127_26/.9)]'
    : 'border-gray-300 text-gray-700 hover:bg-gray-200 hover:text-gray-700'}`
}
