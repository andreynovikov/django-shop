'use client'

import { Swiper, SwiperSlide } from 'swiper/react'
import { Pagination } from 'swiper/modules'

import ReviewItem from '@/components/review/item'

import { ProductReview } from '@/lib/types'

import 'swiper/css'
import 'swiper/css/pagination'

export default function ReviewsCarousel({ reviews }: { reviews: ProductReview[] }) {
  return (
    <Swiper autoHeight pagination={{ clickable: true }} modules={[Pagination]}>
      {reviews.map((review) => (
        <SwiperSlide className="container text-start fs-6" key={review.id}>
          <ReviewItem review={review} last />
        </SwiperSlide>
      ))}
    </Swiper>
  )
}
