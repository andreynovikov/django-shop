'use client'

import { lazy, Suspense } from 'react'

import { useInView } from 'react-intersection-observer'

import { Loading } from '@/components/loading'

import { Product } from '@/lib/types'

const ProductReviews = lazy(() => import('@/components/product/reviews'))

export default function ProductReviewsWrapper({ product }: { product: Product }) {
  const { ref: reviewsRef, inView: reviewsVisible } = useInView({
    rootMargin: '300px',
    triggerOnce: true,
  })

  if (!product.allow_reviews)
    return null

  return (
    <div className="border-t py-12 lg:my-4">
      <div className="container md:pt-2" id="reviews" ref={reviewsRef}>
        {reviewsVisible && (
          <Suspense fallback={<Loading className="text-center" />}>
            <ProductReviews product={product} />
          </Suspense>
        )}
      </div>
    </div>
  )
}