import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductRating from '@/components/product/rating'

import { getProduct } from './load'

const categoryPathname = (path: string[]) => `/catalog/${path.join('/')}/`

// The header is outside the loading boundary, so it is shown while the rest of the page loads
export default async function ProductLayout({ params, children }: LayoutProps<'/products/[code]'>) {
  const { code } = await params
  const product = await getProduct(code)

  const category = product.categories
    .filter(category => !['New', 'promo', 'Discount'].includes(category.slug)) // skip special categories
    .sort((a, b) => b.path.breadcrumbs.length - a.path.breadcrumbs.length)[0] // get the longest path

  const breadcrumbs = category ? [
    ...category.path.breadcrumbs.map((breadcrumb, index, parents) => ({
      label: breadcrumb.name,
      href: categoryPathname(parents.slice(0, index + 1).map(({ slug }) => slug)),
    })),
  ] : []

  return pageContentWrapper({
    title: product.title,
    titleAddon: <>
      {(product.runame || product.whatis) && (
        <span className="text-white opacity-70">
          <span>{product.whatis}</span>
          <span className="d-none d-sm-inline"> {product.runame}</span>
        </span>
      )}
      {product.allow_reviews && <ProductRating product={product.id} anchor="reviews" />}
    </>,
    breadcrumbs,
    dark: true,
    overlapped: true,
    children,
  })
}
