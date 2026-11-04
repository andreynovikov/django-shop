'use client'

import { CSSProperties } from 'react'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import Image from 'next/image'

import { StoreImage } from '@/lib/types'

export default function StoreImageCarousel({ images }: { images: Array<StoreImage> }) {
  return (
    <Swiper
      modules={[FreeMode, Navigation]}
      slidesPerView="auto"
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
      className="sw-store-images"
    >
      <span className="nav-button-prev"><i className="ci-arrow-left"></i></span>
      {images.map((image) => (
        <SwiperSlide
          key={image.order}
          style={{
            '--sw-aspect-ratio': image.image_width > 0 && image.image_height > 0
              ? image.image_width / image.image_height
              : 1
          } as CSSProperties}
        >
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
