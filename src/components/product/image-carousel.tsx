'use client'

import { Dispatch, SetStateAction } from 'react'

import Image from 'next/image'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import { ProductImage } from '@/lib/types'

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
        prevEl: '.nav-button-prev',
        nextEl: '.nav-button-next',
        addIcons: false
      }}
      modules={[FreeMode, Navigation]}
      className={className}
    >
      <span className="nav-button-prev nav-button-sm"><i className="ci-arrow-left"></i></span>
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
      <span className="nav-button-next nav-button-sm"><i className="ci-arrow-right"></i></span>
    </Swiper>
  )
}