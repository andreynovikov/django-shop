'use client'

import { ReactNode } from 'react'

import { NuqsAdapter } from 'nuqs/adapters/next/app'

import { QueryClientProvider } from '@tanstack/react-query'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { getQueryClient } from '@/lib/query-client'

import '@/lib/moment'

// Fewer than cartzilla's: familysew has no login, cart or toasts, and no component here reads the site, session,
// topbar or toolbar contexts
export default function Providers({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <NuqsAdapter>
        {children}
      </NuqsAdapter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
