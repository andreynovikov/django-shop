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
    <div className="border-top my-lg-3 py-5">
      <div className="container pt-md-2" id="reviews" ref={reviewsRef}>
        {reviewsVisible && (
          <Suspense fallback={<Loading className="text-center" />}>
            <ProductReviews product={product} />
          </Suspense>
        )}
      </div>
    </div>
  )
}