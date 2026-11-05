'use client'

import { useState } from 'react'
import Image from 'next/image'

import Lightbox from 'yet-another-react-lightbox'
import { Swiper, SwiperSlide } from 'swiper/react'
import { Pagination } from 'swiper/modules'

import { IconChevronCompactLeft, IconChevronCompactRight, IconX } from '@tabler/icons-react'

import { ProductImage } from '@/lib/types'

import 'swiper/css'
import 'swiper/css/pagination'

// The backend leaves out an empty list of images
export default function ImageCarousel({ image, images = [] }: { image: string, images?: ProductImage[] }) {
  const [currentImageIndex, setCurrentIndex] = useState(-1)

  return (
    <>
      <Swiper
        pagination={{ clickable: true }}
        modules={[Pagination]}
      >
        <SwiperSlide key={image} className="d-flex position-relative" style={{ aspectRatio: "4/3" }}>
          <Image
            src={image}
            fill
            style={{ objectFit: "contain", cursor: "pointer" }}
            onClick={() => setCurrentIndex(0)}
            priority
            loading="eager"
            alt="" />
        </SwiperSlide>
        {images.map((image, index) => (
          <SwiperSlide key={image.src} className="d-flex position-relative" style={{ aspectRatio: "4/3" }}>
            <Image
              src={image.src}
              fill
              style={{ objectFit: "contain", cursor: "pointer" }}
              onClick={() => setCurrentIndex(index + 1)}
              loading="lazy"
              alt="" />
          </SwiperSlide>
        ))}
      </Swiper>
      <Lightbox
        open={currentImageIndex !== -1}
        close={() => setCurrentIndex(-1)}
        index={currentImageIndex}
        on={{ view: ({ index }) => setCurrentIndex(index) }}
        slides={[{
          src: image
        }, ...images]}
        carousel={{
          finite: true
        }}
        render={{
          iconPrev: () => <IconChevronCompactLeft size={64} />,
          iconNext: () => <IconChevronCompactRight size={64} />,
          iconClose: () => <IconX size={64} />
        }}
      />
    </>
  )
}
