import { useState, useEffect } from 'react';
import Script from 'next/script';
import { SessionProvider } from 'next-auth/react';
import { QueryClient, QueryClientProvider, Hydrate } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import RefreshTokenHandler from '@/lib/refresh-token-handler';

import { API, apiClient, categoryKeys, productKeys, userKeys, pageKeys } from '@/lib/queries';

import '@/vendor/nouislider.css';
import '@/vendor/cartzilla/scss/theme.scss';

export default function App({ Component, pageProps: { session, ...pageProps }}) {
    const [interval, setInterval] = useState(0);
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
    queryClient.setQueryDefaults(userKeys.all, { cacheTime: 1000 * 60 * 60, staleTime: Infinity }); // cache for one hour, mark fresh forever
    queryClient.setQueryDefaults(pageKeys.all, { staleTime: Infinity }); // mark fresh forever

    useEffect(() => {
        (async () => {
            const response = await apiClient.get('csrf/');
        })();
    }, []);

    // Use the layout defined at the page level, if available
    const getLayout = Component.getLayout || ((page) => page);

    return (
        <QueryClientProvider client={queryClient}>
            <Hydrate state={pageProps.dehydratedState}>
                <SessionProvider session={session} refetchInterval={interval}>
                    <Script id="bootstrap" src="/js/bootstrap.bundle.js" />
                    { getLayout(<Component {...pageProps} />) }
                    <RefreshTokenHandler setInterval={setInterval} />
                </SessionProvider>
                <ReactQueryDevtools initialIsOpen={false} />
            </Hydrate>
        </QueryClientProvider>
    );
}
