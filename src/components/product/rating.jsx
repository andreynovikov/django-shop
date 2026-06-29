import { useQuery } from '@tanstack/react-query'

import ReviewRating from '@/components/review/rating'

import rupluralize from '@/lib/rupluralize'
import { reviewKeys, getProductRating } from '@/lib/queries'

export default function ProductRating({ product, anchor }) {
  const { data: average, isSuccess } = useQuery({
    queryKey: reviewKeys.rating(product),
    queryFn: () => getProductRating(product)
  })

  if (!isSuccess || average.count === 0)
    return null

  const handleScroll = () => {
    const el = document.getElementById(anchor)
    if (el !== undefined)
      el.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      })
  }

  const props = anchor !== undefined ? { onClick: handleScroll, style: { cursor: 'pointer' } } : {}

  return (
    <div {...props}>
      <ReviewRating value={average.value} />
      <span className="d-inline-block fs-sm text-white opacity-70 align-middle mt-1 ms-1">
        {average.count} {rupluralize(average.count, ['обзор', 'обзора', 'обзоров'])}
      </span>
    </div>
  )
}
