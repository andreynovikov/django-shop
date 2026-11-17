import type { ProductSearchParamsType } from '@/lib/search-params'

// Tags of the data that pages fetch on the server. A static page gets the tags of every request it makes, and when
// the data changes, the backend sends their tags to /api/revalidate, which has the pages rendered again. The backend
// turns each change into the tags it touches, see shop/revalidation.py in django-shop: keep the two lists in step.
// In the browser the tags do nothing.
export const cacheTags = {
  catalog: 'catalog', // the category tree, in the menu of every page
  category: (id: number) => `category:${id}`, // the products right in the category, its adverts
  categoryPath: (path: string[]) => `category-path:${path.join('/')}`, // the category itself
  categoryTree: (id: number) => `category-tree:${id}`, // the products in the category and its subcategories
  firstpage: 'firstpage', // the products of the home page
  product: (code: string) => `product:${code}`,
  actions: 'actions',
  action: (slug: string) => `action:${slug}`, // the sales action and its products
  adverts: (place: string) => `adverts:${place}`,
  stores: 'stores',
  store: (id: number) => `store:${id}`,
  serviceCenters: 'servicecenters',
  pages: 'pages',
  page: (url: string) => `page:${url}`, // by its url, e.g. /about/
  news: 'news',
  reviews: 'reviews',
  site: 'site', // the site's profile
}

export const tagged = (...tags: string[]) => ({ next: { tags } })

// The lists of products that the backend revalidates: those of a category, with its subcategories or without, and
// those of the home page. Lists of the whole catalog, such as the sitemap and the feeds, would be rendered again on
// every change of a product, which an import makes by the hundred: they are rendered again after a while instead,
// as are search results on every request.
export function productListTags(filters: ProductSearchParamsType) {
  return [
    ...(filters.categories ? [cacheTags.category(filters.categories)] : []),
    ...(filters.in_category?.length === 1 ? [cacheTags.categoryTree(filters.in_category[0])] : []),
    ...(filters.firstpage ? [cacheTags.firstpage] : []),
  ]
}
