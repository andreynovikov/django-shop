'use client'

import { ReactNode } from 'react'

import { NuqsAdapter } from 'nuqs/adapters/next/app'

import { QueryClientProvider } from '@tanstack/react-query'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { SiteProvider } from '@/lib/site'
import { SessionProvider } from '@/lib/session'
import { getQueryClient } from '@/lib/query-client'

import '@/lib/moment'

export default function Providers({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <NuqsAdapter>
        <SiteProvider>
          <SessionProvider>
            {children}
          </SessionProvider>
        </SiteProvider>
      </NuqsAdapter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
