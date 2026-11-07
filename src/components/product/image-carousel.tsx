'use client'

import { useEffect, useState } from 'react'

import Image from 'next/image'

import { Swiper, SwiperSlide, SwiperClass } from 'swiper/react'
import { FreeMode, Navigation, Pagination, Thumbs } from 'swiper/modules'
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react'

import { carouselIconSizes, carouselNavClass } from '@/components/ui/carousel'

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

  useEffect(() => {
    const location = window.location.href.split('#')[0]
    if (galleryOpen)
      window.history.pushState({}, '', location + '#galleryOpen')
    else if (window.location.hash.startsWith('#galleryOpen'))
      window.history.back()
    else
      window.history.replaceState({}, '', location)
  }, [galleryOpen])

  useEffect(() => {
    const handleBackEvent = () => {
      setGalleryOpen(false)
    }
    window.addEventListener('popstate', handleBackEvent)
    return () => window.removeEventListener('popstate', handleBackEvent)
  }, [setGalleryOpen])

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
          640: {
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
        <span className={carouselNavClass({ side: 'prev', size: 'lg', fromSm: true })}><IconChevronLeft size={carouselIconSizes.lg} stroke={2} /></span>
        {/* Swiper's styles are unlayered, display utilities on slides need ! */}
        <SwiperSlide key={image} className="relative flex! aspect-4/3">
          <Image
            src={image}
            fill
            style={{ objectFit: "contain", cursor: "pointer" }}
            sizes="(max-width: 1024px) 100vw, 800px"
            onClick={() => setGalleryOpen(true)}
            priority
            itemProp="image"
            loading="eager"
            alt={alt}
            role="button" />
        </SwiperSlide>
        {images && images.map((image, index) => (
          <SwiperSlide key={image.src} className="relative flex! aspect-4/3">
            <Image
              src={image.src}
              fill
              style={{ objectFit: "contain", cursor: "pointer" }}
              sizes="(max-width: 1024px) 100vw, 800px"
              onClick={() => setGalleryOpen(true)}
              loading="lazy"
              alt={`${alt} - №${index + 1}`}
              role="button" />
          </SwiperSlide>
        ))}
        <span className={carouselNavClass({ side: 'next', size: 'lg', fromSm: true })}><IconChevronRight size={carouselIconSizes.lg} stroke={2} /></span>
      </Swiper>
      {images && <Swiper
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
        className="my-2 hidden! md:block!"
      >
        <span className={carouselNavClass({ side: 'prev', size: 'sm' })}><IconChevronLeft size={carouselIconSizes.sm} stroke={2} /></span>
        <SwiperSlide className="relative inline-block! rounded-md border" style={{ width: 80, height: 80 }}>
          <Image
            src={image}
            fill
            style={{ objectFit: 'contain' }}
            sizes="80px"
            loading="lazy"
            alt="" />
        </SwiperSlide>
        {images.map(image => (
          <SwiperSlide key={image.src} className="relative inline-block! rounded-md border" style={{ width: 80, height: 80 }}>
            <Image
              src={image.src}
              fill
              style={{ objectFit: 'contain' }}
              sizes="80px"
              loading="lazy"
              alt="" />
          </SwiperSlide>
        ))}
        <span className={carouselNavClass({ side: 'next', size: 'sm' })}><IconChevronRight size={carouselIconSizes.sm} stroke={2} /></span>
      </Swiper>}
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