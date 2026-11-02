'use client'

import { useEffect } from 'react'

import { eCommerce } from '@/lib/ymec'
import { Product } from '@/lib/types'

export default function ProductImpression({ product }: { product: Product }) {
  useEffect(() => {
    const impressions = [
      ...product.accessories?.map((product, index) => ({
        id: product.id,
        name: product.title,
        price: product.price,
        list: 'Сопутствующие товары',
        position: index + 1
      })) ?? [],
      ...product.similar?.map((product, index) => ({
        id: product.id,
        name: product.title,
        price: product.price,
        list: 'Похожие товары',
        position: index + 1
      })) ?? []
    ]
    eCommerce({
      impressions,
      detail: {
        products: [
          {
            id: `${product.id}`,
            name: `${product.partnumber ? product.partnumber + ' ' : ''}${product.title}`,
            category: `${product.categories[0].name}`,
            brand: `${product.manufacturer.code}`,
            price: `${product.cost}`
          }
        ]
      }
    })
  }, [product])

  return null
}