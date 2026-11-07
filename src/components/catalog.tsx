/* eslint-disable @next/next/no-img-element */

import Link from 'next/link'
import { IconChevronRight } from '@tabler/icons-react'

import { widgetLinkClass, widgetListItemClass } from '@/components/ui/widget'

import { CategoryTree, CategoryTreeItem } from '@/lib/types'
import { columns, rows } from '@/lib/partition'

const first = [3, 4, 5, 6, 744]
const other = [743, 3, 4, 5, 6, 744, 745] // other than these

// A highlighted link to a special category and the props of its arrow
const specialClass = 'mx-0 flex w-full items-center rounded-lg py-2 ps-2 md:mx-2'
const arrow = { size: 12, stroke: 2, className: 'ms-1' }

// Kept free of hooks so App Router server components can render it
export default function Catalog({ categories }: { categories: CategoryTree }) {
  const specialCategories = [null, null] as [CategoryTreeItem | null, CategoryTreeItem | null]
  for (const category of categories) {
    if (category.slug === 'New')
      specialCategories[0] = category
    if (category.slug === 'promo')
      specialCategories[1] = category
  }
  const [categoryNew, categoryPromo] = specialCategories

  const ready = [categoryNew, categoryPromo].every(c => c !== null)

  return (
    <div>
      {ready && (
        <>
          <div className="mb-6 flex flex-wrap justify-between md:flex-nowrap">
            <Link className={`${specialClass} mb-6 bg-info/9`} href={`/catalog/${categoryNew!.slug}/`}>
              {categoryNew!.image && <img className="h-[100px] w-auto" loading="lazy" src={categoryNew!.image} alt={categoryNew!.name} />}
              <div className="px-4 py-6">
                <div className="mb-2 text-h5 text-heading">{categoryNew!.name}</div>
                <div className="text-sm text-info">Посмотреть все<IconChevronRight {...arrow} /></div>
              </div>
            </Link>
            <Link className={`${specialClass} mb-6 bg-warning/9`} href={`/catalog/${categoryPromo!.slug}/`}>
              {categoryPromo!.image && <img className="h-[100px] w-auto" loading="lazy" src={categoryPromo!.image} alt={categoryPromo!.name} />}
              <div className="px-4 py-6">
                <div className="mb-2 text-h5 text-heading">{categoryPromo!.name}</div>
                <div className="text-sm text-warning">Посмотреть все<IconChevronRight {...arrow} /></div>
              </div>
            </Link>
          </div>

          {columns(categories.filter(category => first.includes(category.id)), 2).map((column, index) => (
            <div className="flex flex-wrap md:flex-nowrap" key={index}>
              {column.map((category) => (
                <div className="mx-0 mb-4 w-full md:mx-6" key={category.id}>
                  <div className="mb-4 text-h6">
                    <Link href={`/catalog/${category.slug}/`}>
                      {category.svg_icon && <span className="me-1 inline-block [&_svg]:inline [&_svg]:size-10" dangerouslySetInnerHTML={{ __html: category.svg_icon }}></span>}
                      {category.name}
                    </Link>
                  </div>
                  {category.children && (
                    <div className="ms-2">
                      <div>
                        <ul>
                          {category.children.map((subcategory) => (
                            <li className={`${widgetListItemClass} pb-1`} key={subcategory.id}>
                              <Link className={widgetLinkClass()} href={`/catalog/${category.slug}/${subcategory.slug}/`}>
                                {subcategory.name}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}

          {categories.filter(category => !other.includes(category.id)).map((category, index) => (
            <div className={`mx-0 mb-4 md:mx-6 ${index === 0 ? "mt-6" : ""}`} key={category.id}>
              <div className="mb-4 text-h6">
                <Link href={`/catalog/${category.slug}/`}>
                  {category.svg_icon && <span className="me-1 inline-block [&_svg]:inline [&_svg]:size-10" dangerouslySetInnerHTML={{ __html: category.svg_icon }}></span>}
                  {category.name}
                </Link>
              </div>
              {category.children && (
                <div className="flex flex-wrap md:flex-nowrap">
                  {rows(category.children, 2).map((row, index, arr) => (
                    <div className={`mx-2 w-full ${index === arr.length - 1 ? "pb-2" : ""}`} key={index}>
                      <div className={index === arr.length - 1 ? "md:ms-6" : ""}>
                        <ul>
                          {row.map((subcategory) => (
                            <li className="mb-1 pb-1" key={subcategory.id}>
                              <Link className={widgetLinkClass()} href={`/catalog/${category.slug}/${subcategory.slug}/`}>
                                {subcategory.name}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  )
}
