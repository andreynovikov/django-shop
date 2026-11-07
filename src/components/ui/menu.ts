// Tailwind classes of Cartzilla's dropdown menus: a white box with a shadow, items turn primary on hover

export const menuPopupClass = 'min-w-40 rounded-md border border-gray-300 bg-white py-2 text-left text-body shadow-md'

// A menu that opens on hover of its `group` parent from lg up, below the trigger, as the header's cart and account menus.
// The ::before bridge keeps it open while the pointer moves down to it.
export const hoverMenuClass = `${menuPopupClass} absolute top-full right-0 z-1000 mt-2 hidden animate-slide-up before:absolute before:-top-3 before:right-0 before:h-3 before:w-full lg:group-hover:block`

export const menuItemClass = 'block w-full px-5 py-1.5 text-left text-sm whitespace-nowrap text-gray-700 outline-none transition-colors hover:text-primary data-highlighted:text-primary'

export const menuHeaderClass = 'mb-1 block border-b border-gray-300 px-5 pt-2 pb-3.5 text-sm whitespace-nowrap text-heading'

export const menuDividerClass = 'my-1 border-t border-gray-300'
