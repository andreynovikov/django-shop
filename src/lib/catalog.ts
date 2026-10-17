import { useState, useEffect } from 'react'
import { useNavigation } from './navigation'

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
  const { path } = useNavigation()

  useEffect(() => {
    if (path)
      sessionStorage.setItem('lastCatalogPath', path)
  }, [path])
}

export function useLastCatalog() {
  const [path, setPath] = useState('/')

  useEffect(() => {
    const p = sessionStorage.getItem('lastCatalogPath')
    if (p)
      // TODO: fix set-state-in-effect
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPath(p)
  }, [])

  return path
}
