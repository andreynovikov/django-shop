import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

export const recomendedFilters = {
  enabled: true,
  categories: 473,
  firstpage: true,
  show_on_sw: true
}

export const giftsFilters = {
  enabled: true,
  gift: true,
  show_on_sw: true
}

export const firstPageFilters = {
  enabled: true,
  firstpage: true,
  show_on_sw: true
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
