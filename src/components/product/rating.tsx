'use client'

import { useQuery } from '@tanstack/react-query'

import ReviewRating from '@/components/review/rating'

import rupluralize from '@/lib/rupluralize'
import { reviewKeys, getProductRating } from '@/lib/queries'

export default function ProductRating({ product }: { product: number }) {
  const { data: average, isSuccess } = useQuery({
    queryKey: reviewKeys.rating(product),
    queryFn: () => getProductRating(product)
  })

  if (!isSuccess || average.count === 0)
    return null

  return (
    <>
      <ReviewRating value={average.value} />
      <span className="text-xs tracking-widest text-muted uppercase">
        {average.count} {rupluralize(average.count, ['отзыв', 'отзыва', 'отзывов'])}
      </span>
    </>
  )
}
