'use client'

import { ReactNode } from 'react'

import { NuqsAdapter } from 'nuqs/adapters/next/pages'

import { QueryClientProvider } from '@tanstack/react-query'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { Toast } from '@base-ui/react/toast'

import ToastList from '@/components/toast-list'

import { SiteProvider } from '@/lib/site'
import { SessionProvider } from '@/lib/session'
import { ToolbarProvider } from '@/lib/toolbar'
import { TopbarProvider } from '@/lib/topbar'
import { AppNavigationProvider } from '@/lib/navigation/app-provider'
import { getQueryClient } from '@/lib/query-client'

import '@/lib/moment'

const toastManager = Toast.createToastManager()

export default function Providers({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <NuqsAdapter>
        <SiteProvider>
          <AppNavigationProvider>
            <SessionProvider>
              <Toast.Provider toastManager={toastManager}>
                <TopbarProvider>
                  <ToolbarProvider>
                    {children}
                  </ToolbarProvider>
                </TopbarProvider>
                <Toast.Portal>
                  <Toast.Viewport className="sw-toast-viewport">
                    <ToastList />
                  </Toast.Viewport>
                </Toast.Portal>
              </Toast.Provider>
            </SessionProvider>
          </AppNavigationProvider>
        </SiteProvider>
      </NuqsAdapter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
