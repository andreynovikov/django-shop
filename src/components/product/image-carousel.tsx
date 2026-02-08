'use client'

import { useState } from 'react'

import Image from 'next/image'

import { Swiper, SwiperSlide, SwiperClass } from 'swiper/react'
import { FreeMode, Navigation, Pagination, Thumbs } from 'swiper/modules'

import ImageGallery from './image-gallery'

import { ProductImage } from '@/lib/types'

interface ImageCarouselProps {
  image: string,
  images: ProductImage[],
  alt: string,
}

export default function ImageCarousel({ image, images, alt }: ImageCarouselProps) {
  const [thumbsSwiper, setThumbsSwiper] = useState<SwiperClass>()
  const [currentIndex, setCurrentIndex] = useState(-1)
  const [galleryOpen, setGalleryOpen] = useState(false)


  return (
    <>
      <Swiper
        modules={[Navigation, Pagination, Thumbs]}
        pagination={{
          clickable: true
        }}
        thumbs={{
          swiper: thumbsSwiper
        }}
        breakpoints={{
          0: {
            navigation: false
          },
          576: {
            pagination: false,
            navigation: {
              prevEl: '.nav-button-prev',
              nextEl: '.nav-button-next',
              addIcons: false
            }
          }
        }}
        observer
        observeParents
        onActiveIndexChange={(swiper) => setCurrentIndex(swiper.realIndex)}
      >
        <span className="d-none d-sm-inline nav-button-prev nav-button-lg"><i className="ci-arrow-left"></i></span>
        <SwiperSlide key={image} className="d-flex position-relative" style={{ aspectRatio: "4/3" }}>
          <Image
            src={image}
            fill
            style={{ objectFit: "contain", cursor: "pointer" }}
            sizes="(max-width: 992px) 100vw, 800px"
            onClick={() => setGalleryOpen(true)}
            priority
            itemProp="image"
            loading="eager"
            alt={alt}
            role="button" />
        </SwiperSlide>
        {images && images.map((image, index) => (
          <SwiperSlide key={image.src} className="d-flex position-relative" style={{ aspectRatio: "4/3" }}>
            <Image
              src={image.src}
              fill
              style={{ objectFit: "contain", cursor: "pointer" }}
              sizes="(max-width: 992px) 100vw, 800px"
              onClick={() => setGalleryOpen(true)}
              loading="lazy"
              alt={`${alt} - №${index + 1}`}
              role="button" />
          </SwiperSlide>
        ))}
        <span className="d-none d-sm-inline nav-button-next nav-button-lg"><i className="ci-arrow-right"></i></span>
      </Swiper>
      <Swiper
        slidesPerView={'auto'}
        spaceBetween={10}
        freeMode={true}
        navigation={{
          prevEl: '.nav-button-prev',
          nextEl: '.nav-button-next',
          addIcons: false
        }}
        modules={[FreeMode, Navigation, Thumbs]}
        watchSlidesProgress
        onSwiper={setThumbsSwiper}
        className="d-none d-md-block my-2"
      >
        <span className="nav-button-prev nav-button-sm"><i className="ci-arrow-left"></i></span>
        <SwiperSlide className="d-inline-block position-relative rounded border" style={{ width: 80, height: 80 }}>
          <Image
            src={image}
            fill
            style={{ objectFit: 'contain' }}
            sizes="80px"
            loading="lazy"
            alt="" />
        </SwiperSlide>
        {images.map(image => (
          <SwiperSlide key={image.src} className="d-inline-block position-relative rounded border" style={{ width: 80, height: 80 }}>
            <Image
              src={image.src}
              fill
              style={{ objectFit: 'contain' }}
              sizes="80px"
              loading="lazy"
              alt="" />
          </SwiperSlide>
        ))}
        <span className="nav-button-next nav-button-sm"><i className="ci-arrow-right"></i></span>
      </Swiper>
      <ImageGallery
        currentImage={currentIndex}
        images={[
          image,
          ...(images ?? []).map(image => image.src)
        ]}
        open={galleryOpen}
        setOpen={setGalleryOpen} />
    </>
  )
}