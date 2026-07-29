import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

export const recomendedProductsFilters = {
  enabled: true,
  categories: 743,
  firstpage: true,
}

export const giftProductsFilters = {
  enabled: true,
  gift: true,
  firstpage: true,
}

export const newProductsFilters = {
  enabled: true,
  isnew: true,
  firstpage: true,
}

export default function useCatalog() {
  const router = useRouter()

  useEffect(() => {
    sessionStorage.setItem('lastCatalogPath', router.asPath)
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [])
}

export function useLastCatalog() {
  const [path, setPath] = useState('/')

  useEffect(() => {
    const p = sessionStorage.getItem('lastCatalogPath')
    if (p)
      setPath(p)
  }, [])

  return path
}
