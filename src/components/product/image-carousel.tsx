'use client'

import { Dispatch, SetStateAction } from 'react'

import Image from 'next/image'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

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
            navigation={true}
            modules={[FreeMode, Navigation]}
            className={className}
        >
            {images.map(image => (
                <SwiperSlide key={image.src} className="d-inline-block w-auto">
                    <div onClick={() => setImage(image.src)} className="rounded border" role="button">
                        <Image
                            src={image.thumbnail.src}
                            width={image.thumbnail.width}
                            height={image.thumbnail.height}
                            alt="" />
                    </div>
                </SwiperSlide>
            ))}
        </Swiper>
    )
}