import { useState, useEffect, ReactElement, ReactNode } from 'react'
import type { NextPage } from 'next'
import type { AppProps } from 'next/app'


import { NuqsAdapter } from 'nuqs/adapters/next/pages'
import { QueryClient, QueryClientProvider, HydrationBoundary } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { SiteProvider } from '@/lib/site';
import { SessionProvider } from '@/lib/session';
import { ToolbarProvider } from '@/lib/toolbar';
import { apiClient, categoryKeys, productKeys, pageKeys } from '@/lib/queries';

import 'simplebar-react/dist/simplebar.min.css';
import '@/vendor/nouislider.css'; // price filter // TODO: this breaks external font import
import 'tiny-slider/dist/tiny-slider.css'; // carousel
import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import '../styles.scss';

import moment, { type MomentInput, type Moment } from 'moment';
import 'moment/locale/ru';

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

export type NextPageWithLayout<P = object, IP = P> = NextPage<P, IP> & {
  getLayout?: (page: ReactElement) => ReactNode
}

type AppPropsWithLayout = AppProps & {
  Component: NextPageWithLayout
}

export default function App({ Component, pageProps }: AppPropsWithLayout) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: process.env.NODE_ENV !== "development",
        retry: process.env.NODE_ENV === "development" ? 1 : 3
      }
    }
  }));

  queryClient.setQueryDefaults(categoryKeys.all, { staleTime: Infinity }); // mark fresh forever
  queryClient.setQueryDefaults(productKeys.all, { staleTime: 1000 * 60 * 10 }); // mark fresh for ten minutes
  queryClient.setQueryDefaults(pageKeys.all, { staleTime: Infinity }); // mark fresh forever

  useEffect(() => {
    (async () => {
      await apiClient.get('csrf/');
    })();
  }, []);

  // Use the layout defined at the page level, if available
  const getLayout = Component.getLayout || ((page) => page);

  return (
    <QueryClientProvider client={queryClient}>
      <HydrationBoundary state={pageProps.dehydratedState}>
        <NuqsAdapter>
          <SiteProvider>
            <SessionProvider>
              <ToolbarProvider>
                {getLayout(<Component {...pageProps} />)}
              </ToolbarProvider>
            </SessionProvider>
          </SiteProvider>
        </NuqsAdapter>
        <ReactQueryDevtools initialIsOpen={false} />
      </HydrationBoundary>
    </QueryClientProvider>
  );
}
