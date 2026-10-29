import { Suspense } from 'react'
import { Metadata } from 'next'

import SearchResults, { SearchResultsLoading } from '@/components/product/search-results'

// The page is static, the query is read and the products are loaded in the browser
export const metadata: Metadata = {
  title: 'Поиск товаров',
  robots: { index: false },
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchResultsLoading />}>
      <SearchResults />
    </Suspense>
  )
}
