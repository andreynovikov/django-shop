'use client'

import { AnchorHTMLAttributes, ReactNode, useEffect } from 'react'
import Link from 'next/link'

import { eCommerce } from '@/lib/ymec'
import { Category, ProductInfo } from '@/lib/types'

import { SearchProduct } from '.'

interface ProductCardImpressionProps {
  product: ProductInfo | SearchProduct
  gtmList?: string
  gtmPosition?: number
}

export function ProductCardImpression({ product, gtmList = '', gtmPosition = 0 }: ProductCardImpressionProps) {
  useEffect(() => {
    eCommerce({
      impressions: [{
        id: product.id,
        name: product.title,
        price: product.price,
        list: gtmList,
        position: gtmPosition + 1
      }]
    })
  }, [product, gtmList, gtmPosition])

  return null
}

interface ProductCardLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  product: ProductInfo | SearchProduct
  gtmCategory?: Category
  gtmList?: string
  gtmPosition?: number,
  className?: string,
  children: ReactNode,
}

export function ProductCardLink({ product, gtmCategory = undefined, gtmList = '', gtmPosition = 0, className, children }: ProductCardLinkProps) {
  const productLink = product.variations ? product.variations : `/products/${product.code}`

  const handleClick = () => {
    eCommerce({
      click: {
        products: [{
          id: `${product.id}`,
          name: `${product.partnumber ? product.partnumber + ' ' : ''}${product.title}`,
          price: `${product.cost}`,
          category: gtmCategory?.name ?? null,
          list: gtmList,
          position: gtmPosition + 1
        }]
      }
    })
  }

  return (
    <Link className={className} href={productLink} onClick={handleClick}>
      {children}
    </Link>
  )
}