'use client'

import { useQuery } from '@tanstack/react-query'

import ReviewRating from '@/components/review/rating'

import rupluralize from '@/lib/rupluralize'
import { reviewKeys, getProductRating } from '@/lib/queries'

export default function ProductRating({ product, anchor }: { product: number, anchor: string }) {
  const { data: average, isSuccess } = useQuery({
    queryKey: reviewKeys.rating(product),
    queryFn: () => getProductRating(product)
  })

  if (!isSuccess || average.count === 0)
    return null

  const handleScroll = () => {
    const el = document.getElementById(anchor)
    if (el)
      el.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      })
  }

  const props = anchor !== undefined ? { onClick: handleScroll, style: { cursor: 'pointer' } } : {}

  return (
    <div {...props}>
      <ReviewRating value={average.value} />
      <span className="ms-1 mt-1 inline-block align-middle text-sm text-white opacity-70">
        {average.count} {rupluralize(average.count, ['обзор', 'обзора', 'обзоров'])}
      </span>
    </div>
  )
}
