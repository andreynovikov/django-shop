import { useState, useEffect } from 'react';
import Script from 'next/script';
import { QueryClient, QueryClientProvider, Hydrate } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import { SiteProvider } from '@/lib/site';
import { SessionProvider } from '@/lib/session';
import { apiClient, categoryKeys, productKeys, pageKeys } from '@/lib/queries';

import '@/vendor/nouislider.css'; // price filter // TODO: this breaks external font import
import 'tiny-slider/dist/tiny-slider.css'; // carousel
import 'glightbox/dist/css/glightbox.css'; // image gallery
import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import '../styles.scss';

export default function App({ Component, pageProps: { site, session, ...pageProps }}) {
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
                <SiteProvider site={site}>
                    <SessionProvider session={session}>
                        <Script id="bootstrap" src="/js/bootstrap.bundle.js" />
                        { getLayout(<Component {...pageProps} />) }
                    </SessionProvider>
                </SiteProvider>
                <ReactQueryDevtools initialIsOpen={false} />
            </Hydrate>
        </QueryClientProvider>
    );
}
