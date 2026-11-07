'use client'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react'

import { carouselIconSizes, carouselNavClass } from '@/components/ui/carousel'

import ProductMiniCard from './mini-card'

import { Product, ProductInfo } from '@/lib/types'

const productSwiperProps = {
  slidesPerView: 1,
  spaceBetween: 0,
  breakpoints: {
    640: { slidesPerView: 2 },
    770: { slidesPerView: 3 },
    1100: { slidesPerView: 4 },
  },
  freeMode: {
    enabled: true,
    sticky: true,
  },
  navigation: {
    prevEl: '.nav-button-prev',
    nextEl: '.nav-button-next',
    addIcons: false
  },
  modules: [FreeMode, Navigation]
}

interface RelatedProductsCarouselProps {
  product: Product
  related: Array<ProductInfo>
  title: string
}

export default function RelatedProductsCarousel({ product, related, title }: RelatedProductsCarouselProps) {
  return <>
    <h2 className="mb-3 pb-6 text-center text-h3">{title} {product.title}</h2>
    <Swiper {...productSwiperProps}>
      <span className={carouselNavClass({ side: 'prev' })}><IconChevronLeft size={carouselIconSizes.md} stroke={2} /></span>
      {related.map((accessory) => (
        <SwiperSlide key={accessory.id} className="px-4">
          <ProductMiniCard product={accessory} />
        </SwiperSlide>
      ))}
      <span className={carouselNavClass({ side: 'next' })}><IconChevronRight size={carouselIconSizes.md} stroke={2} /></span>
    </Swiper>
  </>
}