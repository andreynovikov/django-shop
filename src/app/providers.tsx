'use client'

import { ReactNode } from 'react'

import { NuqsAdapter } from 'nuqs/adapters/next/app'

import { QueryClientProvider } from '@tanstack/react-query'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { Toast } from '@base-ui/react/toast'

import ToastList from '@/components/toast-list'

import { SiteProvider } from '@/lib/site'
import { SessionProvider } from '@/lib/session'
import { ToolbarProvider } from '@/lib/toolbar'
import { TopbarProvider } from '@/lib/topbar'
import { getQueryClient } from '@/lib/query-client'

import '@/lib/moment'

const toastManager = Toast.createToastManager()

export default function Providers({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <NuqsAdapter>
        <SiteProvider>
          <SessionProvider>
            <Toast.Provider toastManager={toastManager}>
              <TopbarProvider>
                <ToolbarProvider>
                  {children}
                </ToolbarProvider>
              </TopbarProvider>
              <Toast.Portal>
                <Toast.Viewport aria-label="Уведомления" className="fixed right-auto bottom-4 left-4 z-1 mx-auto w-[250px] min-[500px]:bottom-8 min-[500px]:left-8 min-[500px]:w-[300px]">
                  <ToastList />
                </Toast.Viewport>
              </Toast.Portal>
            </Toast.Provider>
          </SessionProvider>
        </SiteProvider>
      </NuqsAdapter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
