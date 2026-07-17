import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

export const baseFilters = {
  enabled: true,
  show_on_sw: true,
}

export const recomendedProductsFilters = {
  ...baseFilters,
  categories: 473,
  firstpage: true,
}

export const giftProductsFilters = {
  ...baseFilters,
  gift: true,
  firstpage: true,
}

export const newProductsFilters = {
  ...baseFilters,
  isnew: true,
  firstpage: true,
}

export function useCatalog() {
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
