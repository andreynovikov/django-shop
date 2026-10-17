'use client'

import { ReactNode } from 'react'

import { NuqsAdapter } from 'nuqs/adapters/next/pages'

import { environmentManager, QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { Toast } from '@base-ui/react/toast'

import ToastList from '@/components/toast-list'

import { SiteProvider } from '@/lib/site'
import { SessionProvider } from '@/lib/session'
import { ToolbarProvider } from '@/lib/toolbar'
import { TopbarProvider } from '@/lib/topbar'
import { AppNavigationProvider } from '@/lib/navigation/app-provider'
import { categoryKeys, productKeys, pageKeys } from '@/lib/queries'

import moment, { type MomentInput, type Moment } from 'moment'
import 'moment/locale/ru'

moment.locale('ru');
moment.updateLocale('ru', {
  monthsShort: {
    format: 'янв_фев_мар_апр_мая_июн_июл_авг_сен_окт_ноя_дек'.split('_'),
    standalone: 'янв_фев_март_апр_май_июнь_июль_авг_сен_окт_ноя_дек'.split('_')
  },
  calendar: {
    lastWeek: function (m?: MomentInput, now?: Moment) {
      if (now?.week() !== (this as unknown as Moment).week()) {
        switch ((this as unknown as Moment).day()) {
          case 0:
            return '[В прошлое] dddd';
          case 1:
          case 2:
          case 4:
            return '[В прошлый] dddd';
          case 3:
          case 5:
          case 6:
            return '[В прошлую] dddd';
          default:
            return '[В прошлое] dddd';
        }
      } else {
        if ((this as unknown as Moment).day() === 2) {
          return '[Во] dddd';
        } else {
          return '[В] dddd';
        }
      }
    }
  },
});

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: process.env.NODE_ENV !== "development",
        retry: process.env.NODE_ENV === "development" ? 1 : 5,
        // With SSR, we usually want to set some default staleTime
        // above 0 to avoid refetching immediately on the client
        staleTime: 60 * 1000,
      },
    },
  })
}

let browserQueryClient: QueryClient | undefined = undefined

function getQueryClient() {
  if (environmentManager.isServer()) {
    // Server: always make a new query client
    return makeQueryClient()
  } else {
    // Browser: make a new query client if we don't already have one
    // This is very important, so we don't re-make a new client if React
    // suspends during the initial render. This may not be needed if we
    // have a suspense boundary BELOW the creation of the query client
    if (!browserQueryClient) browserQueryClient = makeQueryClient()
    return browserQueryClient
  }
}

const toastManager = Toast.createToastManager()

export default function Providers({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient()

  queryClient.setQueryDefaults(categoryKeys.all, { staleTime: Infinity }); // mark fresh forever
  queryClient.setQueryDefaults(productKeys.all, { staleTime: 1000 * 60 * 10 }); // mark fresh for ten minutes
  queryClient.setQueryDefaults(pageKeys.all, { staleTime: Infinity }); // mark fresh forever

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
