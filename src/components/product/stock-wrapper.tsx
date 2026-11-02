'use client'

import { lazy, Suspense } from 'react'

import { Loading } from '@/components/loading'

const ProductStock = lazy(() => import('@/components/product/stock'))

export default function ProductStockWrapper({ id }: { id: number }) {
  return (
    <Suspense fallback={<Loading className="text-center" />}>
      <ProductStock id={id} />
    </Suspense>
  )
}