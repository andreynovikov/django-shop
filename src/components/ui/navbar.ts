// Tailwind classes of the header and footer navbars, light gray bars as Bootstrap's .navbar-light .bg-light.
// Their links are in a column below lg and in a row from lg up.

// The bar
export const navbarClass = 'flex flex-wrap items-center justify-between rounded-md border bg-light py-2 lg:flex-nowrap'

// Its content, as Bootstrap's .container-fluid
export const navbarContentClass = 'flex w-full flex-wrap items-center justify-between px-3 lg:flex-nowrap'

// The links
export const navLinksClass = 'flex flex-col lg:flex-row'
export const navLinkClass = 'block py-2 font-bold text-black/65 no-underline transition-colors hover:text-black/80 lg:px-[.8rem]'
