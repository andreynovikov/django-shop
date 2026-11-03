'use client'

import { Suspense } from 'react'

import { useCatalog } from '@/lib/catalog/hooks'

function CatalogRecorder() {
  useCatalog()

  return null
}

// The boundary keeps the page around it in the static HTML, the path is recorded after hydration
export default function CurrentCatalog() {
  return (
    <Suspense>
      <CatalogRecorder />
    </Suspense>
  )
}
