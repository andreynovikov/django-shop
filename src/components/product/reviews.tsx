'use client'

import { useQuery } from '@tanstack/react-query'

import ReviewItem from '@/components/review/item'

import { reviewKeys, loadProductReviews } from '@/lib/queries'

// Reviews are read-only, the site has no user accounts
export default function ProductReviews({ productId }: { productId: number }) {
  const { data: reviews, isSuccess } = useQuery({
    queryKey: reviewKeys.list(productId),
    queryFn: () => loadProductReviews(productId)
  })

  if (!isSuccess)
    return (
      <div className="px-3">Загружается...</div>
    )

  return (
    <div className="mb-12 lg:w-5/6 xl:w-3/4">
      {reviews.results.length > 0 ? (
        reviews.results.map((review, index) => <ReviewItem review={review} last={index === reviews.results.length - 1} key={review.id} />)
      ) : (
        <div className="px-3">Нет отзывов об этом товаре.</div>
      )}
    </div>
  )
}
