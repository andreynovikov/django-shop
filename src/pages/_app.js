import { useState, useEffect } from 'react';
import Script from 'next/script';
import { QueryClient, QueryClientProvider, Hydrate } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import { SessionProvider } from '@/lib/session';
import { apiClient, categoryKeys, productKeys, pageKeys } from '@/lib/queries';

import 'tiny-slider/dist/tiny-slider.css';
import '@/vendor/nouislider.css';  // TODO: this breaks external font import
import '@/vendor/lightgallery/css/lightgallery.css';
import '@/vendor/cartzilla/scss/theme.scss';

export default function App({ Component, pageProps: { session, ...pageProps }}) {
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                refetchOnWindowFocus: process.env.NODE_ENV !== "development",
                retry: process.env.NODE_ENV === "development" ? 1 : 3
            }
        }
    }));

    queryClient.setQueryDefaults(categoryKeys.all, { cacheTime: 1000 * 60 * 10, staleTime: Infinity }); // cache for ten minutes, mark fresh forever
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
            <Hydrate state={pageProps.dehydratedState}>
                <SessionProvider session={session}>
                    <Script id="bootstrap" src="/js/bootstrap.bundle.js" />
                    { getLayout(<Component {...pageProps} />) }
                </SessionProvider>
                <ReactQueryDevtools initialIsOpen={false} />
            </Hydrate>
        </QueryClientProvider>
    );
}
