'use client'

import Image from 'next/image'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import { ProductImage } from '@/lib/types'

import 'swiper/css'
import 'swiper/css/free-mode'
import 'swiper/css/navigation'

interface ImageCarouselProps {
    images: ProductImage[],
    className?: string
}

export default function ImageCarousel({ images, className }: ImageCarouselProps) {
    return (
        <Swiper
            slidesPerView={'auto'}
            spaceBetween={10}
            freeMode={true}
            navigation={true}
            modules={[FreeMode, Navigation]}
            className={className}
        >
            {images.map(image => (
                <SwiperSlide key={image.src} className="d-inline-block w-auto">
                    <a href={image.src} className="glightbox gallery-item rounded border">
                        <Image
                            src={image.thumbnail.src}
                            width={image.thumbnail.width}
                            height={image.thumbnail.height}
                            alt="" />
                    </a>
                </SwiperSlide>
            ))}
        </Swiper>
    )
}