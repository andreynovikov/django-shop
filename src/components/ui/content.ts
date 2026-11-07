// Classes of a container of HTML stored by the backend: Tailwind's typography plugin, tuned to look like Cartzilla's
// reboot (headings of weight 500 with .75rem below, 1rem below paragraphs and lists, links not underlined).
// `backend-content` scopes the transitional styles of the Bootstrap classes the HTML still has (backend-content.css);
// remove it from here once django-shop's `tailwindize_html --write` has converted the database.

const prose = [
  'backend-content prose max-w-none leading-normal',
  '[--tw-prose-headings:var(--color-heading)] [--tw-prose-links:var(--color-primary)]',
  '[--tw-prose-bold:inherit] [--tw-prose-bullets:var(--color-gray-600)] [--tw-prose-counters:var(--color-gray-600)]',
  'prose-headings:mt-0 prose-headings:mb-3 prose-h1:text-h1 prose-h2:text-h2 prose-h3:text-h3 prose-h4:text-h4',
  '[&_:is(h5,h6)]:mt-0 [&_:is(h5,h6)]:mb-3 [&_h5]:text-h5 [&_h6]:text-h6 [&_div+h5]:mt-2', // a feature: picture, title, text
  'prose-p:mt-0 prose-p:mb-4 prose-ul:mt-0 prose-ul:mb-4 prose-ul:ps-8 prose-ol:mt-0 prose-ol:mb-4 prose-ol:ps-8',
  'prose-li:my-0 prose-li:ps-0 prose-a:font-normal prose-a:no-underline prose-strong:font-bold',
  'prose-img:my-0 prose-video:my-0 prose-figure:my-0 prose-hr:my-0',
].join(' ')

const sizes = {
  base: '',
  sm: 'text-sm', // e.g. field help
  ms: 'text-ms', // e.g. the product card's short description
}

// `muted` text is gray, e.g. in a popover
export function contentClass({ size = 'base', muted = false }: { size?: keyof typeof sizes, muted?: boolean } = {}) {
  return `${prose} ${sizes[size]} ${muted ? 'text-muted [--tw-prose-body:var(--color-muted)]' : 'text-body [--tw-prose-body:var(--color-body)]'}`
}

// Adverts are banners styled inline by the editors. Their headings, paragraphs and pictures relied on Bootstrap's reboot:
// headings of weight 500 and line height 1.2 with .75rem below, 1rem below paragraphs, inline SVGs (e.g. a logo in a
// heading) in the middle of the line; the inline styles override these.
export const advertClass = 'backend-content [&_:is(h1,h2,h3,h4,h5,h6)]:mb-3 [&_:is(h1,h2,h3,h4,h5,h6)]:leading-[1.2] [&_:is(h1,h2,h3,h4,h5,h6)]:font-medium [&_p]:mb-4 [&_svg]:inline [&_svg]:align-middle'
