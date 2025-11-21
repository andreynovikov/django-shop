import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

export const recomendedFilters = [
  { field: 'enabled', value: 1 },
  { field: 'recomended', value: 1 },
  { field: 'show_on_sw', value: 1 }
]

export const giftsFilters = [
  { field: 'enabled', value: 1 },
  { field: 'gift', value: 1 },
  { field: 'show_on_sw', value: 1 }
]

export const firstPageFilters = [
  { field: 'enabled', value: 1 },
  { field: 'firstpage', value: 1 },
  { field: 'show_on_sw', value: 1 }
]

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
