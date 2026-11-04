'use client'

import { Swiper, SwiperSlide, SwiperClass } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import Image from 'next/image'

import { StoreImage } from '@/lib/types'

export default function StoreImageCarousel({ images }: { images: Array<StoreImage> }) {
  return (
    <Swiper
      modules={[FreeMode, Navigation]}
      slidesPerView={5}
      spaceBetween={10}
      freeMode={{
        enabled: true,
        sticky: true,
      }}
      navigation={{
        prevEl: '.nav-button-prev',
        nextEl: '.nav-button-next',
        addIcons: false
      }}
    >
      <span className="nav-button-prev"><i className="ci-arrow-left"></i></span>
      {images.map((image) => (
        <SwiperSlide key={image.order}>
          <Image
            src={image.image}
            width={image.image_width}
            height={image.image_height}
            loading="lazy"
            alt={image.kind} />
        </SwiperSlide>
      ))}
      <span className="nav-button-next"><i className="ci-arrow-right"></i></span>
    </Swiper>
  )
}