import { useMemo } from 'react'

import { useQuery } from '@tanstack/react-query'

import ProductCard from '@/components/product/card'
import { ProductResult } from "@/lib/diginetica"

import { productKeys, loadProductInfo } from '@/lib/queries'

const codeRegex = /products\/(.+)(\/|\.html)/

function resultToProduct(result: ProductResult) {
  const matches = result.link_url.match(codeRegex)
  return {
    id: Number(result.id),
    code: matches !== null ? matches[1] : undefined,
    enabled: true,
    variations: false,
    instock: result.available,
    title: result.name,
    price: Number(result.price),
    cost: Number(result.price),
    image: result.image_url,
  }
}

export default function ProductSearchCard({ result, position }: { result: ProductResult, position: number }) {
  const searchProduct = useMemo(() => resultToProduct(result), [result])

  const { data: product, isSuccess } = useQuery({
    queryKey: productKeys.info(result.id),
    queryFn: () => loadProductInfo(result.id),
  })

  return <ProductCard product={isSuccess ? product : searchProduct} gtmList="Результаты поиска" gtmPosition={position} />
}