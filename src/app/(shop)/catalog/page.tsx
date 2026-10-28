import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import Catalog from '@/components/catalog'

import { loadCategories } from '@/lib/queries'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Каталог',
}

export default async function CatalogPage() {
  const categories = await loadCategories()

  return pageContentWrapper({
    title: 'Каталог',
    dark: true,
    children: (
      <div className="container py-5 mb-2 mb-md-4">
        <Catalog categories={categories} />
      </div>
    )
  })
}
