'use client'

import { Swiper, SwiperSlide } from 'swiper/react'
import { FreeMode, Navigation } from 'swiper/modules'

import ProductMiniCard from './mini-card'

import { Product, ProductInfo } from '@/lib/types'

const productSwiperProps = {
  slidesPerView: 1,
  spaceBetween: 0,
  breakpoints: {
    500: { slidesPerView: 2 },
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
    <h2 className="h3 text-center pb-4">{title} {product.title}</h2>
    <Swiper {...productSwiperProps}>
      <span className="nav-button-prev"><i className="ci-arrow-left"></i></span>
      {related.map((accessory) => (
        <SwiperSlide key={accessory.id} className="px-4">
          <ProductMiniCard product={accessory} />
        </SwiperSlide>
      ))}
      <span className="nav-button-next"><i className="ci-arrow-right"></i></span>
    </Swiper>
  </>
}