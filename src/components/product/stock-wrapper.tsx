'use client'

import { Suspense } from 'react'

import { Loading } from '@/components/loading'

import { lazyWithReload } from '@/lib/lazy'

const ProductStock = lazyWithReload(() => import('@/components/product/stock'))

export default function ProductStockWrapper({ id }: { id: number }) {
  return (
    <Suspense fallback={<Loading className="text-center" />}>
      <ProductStock id={id} />
    </Suspense>
  )
}