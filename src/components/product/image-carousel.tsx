'use client'

import { Dispatch, SetStateAction } from 'react'

import Image from 'next/image'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import { IconCircleChevronLeftFilled, IconCircleChevronRightFilled } from '@tabler/icons-react'

import { ProductImage } from '@/lib/types'

import 'swiper/css'
import 'swiper/css/free-mode'
import 'swiper/css/navigation'

interface ImageCarouselProps {
  images: ProductImage[],
  setImage: Dispatch<SetStateAction<string>>
  className?: string
}

export default function ImageCarousel({ images, setImage, className }: ImageCarouselProps) {
  return (
    <Swiper
      slidesPerView={'auto'}
      spaceBetween={10}
      freeMode={true}
      navigation={{
        prevEl: '.swiper-button-prev',
        nextEl: '.swiper-button-next'
      }}
      modules={[FreeMode, Navigation]}
      className={className}
    >
      <span className="swiper-button-prev text-light"><IconCircleChevronLeftFilled /></span>
      {images.map(image => (
        <SwiperSlide key={image.src} className="d-inline-block w-auto">
          <div onClick={() => setImage(image.src)} className="position-relative rounded border" style={{ width: 80, height: 80 }} role="button">
            <Image
              src={image.src}
              fill
              style={{ objectFit: 'contain' }}
              sizes="80px"
              loading="lazy"
              alt="" />
          </div>
        </SwiperSlide>
      ))}
      <span className="swiper-button-next text-light"><IconCircleChevronRightFilled /></span>
    </Swiper>
  )
}