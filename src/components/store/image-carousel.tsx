'use client'

import { CSSProperties } from 'react'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import Image from 'next/image'
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react'

import { carouselIconSizes, carouselNavClass } from '@/components/ui/carousel'

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
      className="[--sw-store-image-height:200px] md:[--sw-store-image-height:260px] xl:[--sw-store-image-height:320px]"
    >
      <span className={carouselNavClass({ side: 'prev' })}><IconChevronLeft size={carouselIconSizes.md} stroke={2} /></span>
      {images.map((image) => (
        // same height for all slides, the width follows the image's aspect ratio; Swiper's own CSS is unlayered
        <SwiperSlide
          key={image.order}
          className="h-(--sw-store-image-height)! w-[calc(var(--sw-store-image-height)*var(--sw-aspect-ratio,1))]!"
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
            className="block size-full object-cover"
            alt={image.kind} />
        </SwiperSlide>
      ))}
      <span className={carouselNavClass({ side: 'next' })}><IconChevronRight size={carouselIconSizes.md} stroke={2} /></span>
    </Swiper>
  )
}
