import { useState, ReactElement, ReactNode } from 'react'
import type { NextPage } from 'next'
import type { AppProps } from 'next/app'
import localFont from 'next/font/local'

import { NuqsAdapter } from 'nuqs/adapters/next/pages'
import { QueryClientProvider, HydrationBoundary } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { Toast } from '@base-ui/react/toast'

import ToastList from '@/components/toast-list'

import { SiteProvider } from '@/lib/site';
import { SessionProvider } from '@/lib/session'
import { TopbarProvider } from '@/lib/topbar'
import { ToolbarProvider } from '@/lib/toolbar'
import { PagesNavigationProvider } from '@/lib/navigation/pages-provider'
import { makeQueryClient } from '@/lib/query-client'

import 'simplebar-react/dist/simplebar.min.css'
import 'swiper/css'
import 'swiper/css/free-mode'
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import '../styles.scss';

import '@/lib/moment'

const rubik = localFont({
  src: [
    {
      path: '../assets/fonts/Rubik/Rubik-VariableFont_wght.ttf',
      style: 'normal',
    }, {
      path: '../assets/fonts/Rubik/Rubik-Italic-VariableFont_wght.ttf',
      style: 'italic',
    }
  ],
  fallback: ['sans-serif'],
  variable: '--font-rubik',
})

const toastManager = Toast.createToastManager()

export type NextPageWithLayout<P = object, IP = P> = NextPage<P, IP> & {
  getLayout?: (page: ReactElement, pageProps: P) => ReactNode
}

type AppPropsWithLayout = AppProps & {
  Component: NextPageWithLayout
}

export default function App({ Component, pageProps }: AppPropsWithLayout) {
  const [queryClient] = useState(() => makeQueryClient())

  // Use the layout defined at the page level, if available
  const getLayout = Component.getLayout ?? ((page) => page)

  return (
    <QueryClientProvider client={queryClient}>
      <HydrationBoundary state={pageProps.dehydratedState}>
        <NuqsAdapter>
          <SiteProvider>
            <PagesNavigationProvider>
              <SessionProvider>
                <Toast.Provider toastManager={toastManager}>
                  <TopbarProvider>
                    <ToolbarProvider>
                      <div className={rubik.variable}>
                        {getLayout(<Component {...pageProps} />, pageProps)}
                      </div>
                    </ToolbarProvider>
                  </TopbarProvider>
                  <Toast.Portal>
                    <Toast.Viewport className="sw-toast-viewport">
                      <ToastList />
                    </Toast.Viewport>
                  </Toast.Portal>
                </Toast.Provider>
              </SessionProvider>
            </PagesNavigationProvider>
          </SiteProvider>
        </NuqsAdapter>
        <ReactQueryDevtools initialIsOpen={false} />
      </HydrationBoundary>
    </QueryClientProvider>
  )
}
