import { createContext, ReactNode, useContext, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { siteKeys, loadCurrentSite } from '@/lib/queries'
import { Site } from './types'

type SiteStatusType = 'loading' | 'success' | 'error'
interface SiteContextType {
  site: Partial<Site>
  status: SiteStatusType
}

export const SiteContext = createContext<SiteContextType>({ status: 'loading', site: {} })

export function useSite() {
  return useContext(SiteContext)
}

interface SiteProviderProps {
  children: ReactNode;
}

export function SiteProvider({ children }: SiteProviderProps) {
  const { data: site, isSuccess, isLoading } = useQuery({
    queryKey: siteKeys.current(),
    queryFn: () => loadCurrentSite(),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  const value = useMemo(() => ({
    site: (site ?? {}) as Partial<Site>,
    status: (isLoading ? 'loading' : isSuccess ? 'success' : 'error') as SiteStatusType
  }), [site, isLoading, isSuccess])

  return (
    <SiteContext.Provider value={value}>{children}</SiteContext.Provider>
  )
}
