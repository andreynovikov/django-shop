import { cache } from 'react'
import { notFound } from 'next/navigation'

import { HttpError, loadProductByCode } from '@/lib/queries'

// Shared by the layout, generateMetadata and the page, so the product is fetched once per render
export const getProduct = cache(async (code: string) => {
  try {
    return await loadProductByCode(code)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})
