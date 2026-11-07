/* eslint-disable @next/next/no-img-element */
import Link from 'next/link'

// A column with the gifts pattern behind it, the white box under an icon hides the pattern there
const columnClass = 'mb-7.5 bg-[url(/i/categories/gifts.svg)] bg-no-repeat text-center lg:px-2'
const categoryClass = `${columnClass} w-1/2 md:w-1/3 lg:w-auto`
// From lg up the empty columns at both ends fill the rest of the row with the pattern
const fillerClass = `${columnClass} hidden grow lg:flex`
// Cartzilla's .nav-link without side padding: gray, primary on hover
const titleClass = 'block py-3 text-gray-700 transition-colors hover:text-primary'

const categories = [
  { href: '/catalog/sewing_machines/', icon: 'sewing.svg', alt: 'Механические швейные машины', title: <>Механические<br />швейные машины</> },
  { href: '/catalog/comp_sewing_machines/', icon: 'compsewing.svg', alt: 'Электронные швейные машины', title: <>Электронные<br />швейные машины</> },
  { href: '/catalog/sewing_embroidery_machines/', icon: 'embroidery.svg', alt: 'Швейно-вышивальные машины', title: <>Машины<br />с&nbsp;вышивкой</> },
  { href: '/catalog/overlock/', icon: 'overlock.svg', alt: 'Оверлоки и коверлоки', title: 'Оверлоки' },
  { href: '/catalog/coverpro/', icon: 'prom.svg', alt: 'Плоскошовные машины', title: <>Плоскошовные<br />машины</> },
  { href: '/catalog/accessories/', icon: 'accessories.svg', alt: 'Аксессуары', title: 'Аксессуары' },
]

export default function TopCategoriesCard() {
  return (
    <div className="relative mx-1 flex min-w-0 flex-col rounded-lg bg-white shadow-lg md:mx-12 xl:mx-0">
      <div className="px-4 pt-5 pb-0">
        <div className="flex flex-wrap justify-center lg:-mx-2">
          <div className={fillerClass}>
            <div className="bg-white"></div>
            <div className={titleClass}></div>
          </div>
          {categories.map(({ href, icon, alt, title }) => (
            <div className={categoryClass} key={href}>
              <Link href={href}>
                <div className="bg-white"><img src={`/i/categories/${icon}`} alt={alt} className="inline align-middle" /></div>
                <div className={titleClass}>{title}</div>
              </Link>
            </div>
          ))}
          <div className={fillerClass}>
            <div className="bg-white"></div>
            <div className={titleClass}></div>
          </div>
        </div>
      </div>
    </div>
  )
}
