import type { MetadataRoute } from 'next'

import { getCategoryDescendants } from '@/lib/categories'
import { loadCategories, loadCurrentSite, loadPages, loadProducts, loadSalesActions, loadStores, loadTopics } from '@/lib/queries'
import { Category, FlatPageInfo, ForumTopic, PaginatedResult, Product, SalesAction, Store } from '@/lib/types'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = await loadCurrentSite()
  const now = new Date();

  // Static routes

  const routes: MetadataRoute.Sitemap = [
    {
      url: `${site.url_prefix}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.5,
    },
    {
      url: `${site.url_prefix}/catalog/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.5,
    },
    {
      url: `${site.url_prefix}/service/`,
      lastModified: now,
      changeFrequency: 'monthly',
      priority: 0.5,
    },
  ]

  // Categories

  const categories = await loadCategories() as Category[]
  categories.forEach(category => {
    routes.push({
      url: `${site.url_prefix}/catalog/${category.slug}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.8,
    })

    getCategoryDescendants(category).forEach(category => {
      routes.push({
        url: `${site.url_prefix}/catalog/${category.path.join('/')}/`,
        lastModified: now,
        changeFrequency: 'weekly',
        priority: 0.8,
      })
    })
  })

  // Products

  const filters = {
    enabled: true,
    price: [0, 10000000],
    in_category: categories.map(category => category.id),
    variations: '',
  }
  const pageSize = 1000
  const order = 'id'
  let currentPage = 1

  while (true) {
    const productsPage = await loadProducts(currentPage, pageSize, filters, order) as PaginatedResult<Product>
    productsPage.results.forEach(product => {
      routes.push({
        url: `${site.url_prefix}/products/${product.code}/`,
        lastModified: now,
        changeFrequency: 'weekly',
        priority: 1.0,
      })
    })
    if (productsPage.totalPages <= currentPage)
      break;
    currentPage++
  }

  // Stores

  const stores = await loadStores() as Store[]
  stores.filter(store => store.logo === 'sewingworld').forEach(store => {
    routes.push({
      url: `${site.url_prefix}/stores/${store.id}/`,
      lastModified: now,
      changeFrequency: 'monthly',
      priority: 0.3,
    })
  })

  // Sales actions

  const actions = await loadSalesActions() as SalesAction[]
  actions.forEach(action => {
    routes.push({
      url: `${site.url_prefix}/actions/${action.slug}/`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.7,
    })
  })

  // Flat pages

  const pages = await loadPages() as FlatPageInfo[]
  pages.filter(page => !page.url.match('^\/(help|dialog)\/.*')).forEach(page => {
    routes.push({
      url: `${site.url_prefix}/pages${page.url}`,
      lastModified: now,
      changeFrequency: 'monthly',
      priority: 0.3,
    })
  })

  // Forum

  const forums = await loadTopics() as ForumTopic[]
  forums.forEach(forum => {
    forum.threads.forEach(thread => {
      routes.push({
        url: `${site.url_prefix}/oldforum/thread/${thread.id}/`,
        lastModified: thread.mtime ? new Date(thread.mtime) : now,
        changeFrequency: 'never',
        priority: 0.2,
      })
    })
  })

  return routes
}