import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { QueryClient, QueryClientProvider, Hydrate } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import SSRProvider from 'react-bootstrap/SSRProvider';

import TagManager from 'react-gtm-module';
import ym, { YMInitializer } from 'react-yandex-metrika';

import { SiteProvider } from '@/lib/site';
import { SessionProvider } from '@/lib/session';
import { apiClient, categoryKeys, productKeys, pageKeys } from '@/lib/queries';

import { config } from '@fortawesome/fontawesome-svg-core';
import '@fortawesome/fontawesome-svg-core/styles.css';
config.autoAddCss = false;

//import 'glightbox/dist/css/glightbox.css';
import '../styles.scss';

export default function App({ Component, pageProps: { site, session, ...pageProps }}) {
    const router = useRouter();

    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                refetchOnWindowFocus: process.env.NODE_ENV !== "development",
                retry: (failureCount, error) => {
                    if (error.request.status === 404)
                        return 0;
                    else
                        return process.env.NODE_ENV === "development" ? 1 : 3;
                }
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
        if (!!process.env.NEXT_PUBLIC_GTM_ID) {
            TagManager.initialize({gtmId: process.env.NEXT_PUBLIC_GTM_ID});
            TagManager.dataLayer({
                dataLayer: {
                    event: 'pageview',
                    page: router.asPath
                }
            });
        }
        if (!!process.env.NEXT_PUBLIC_YM_COUNTER_ID) {
            ym('hit', router.asPath);
        }
    }, []);

    useEffect(() => {
        const handleRouteChange = (url) => {
            if (typeof window !== 'undefined' && !!process.env.NEXT_PUBLIC_GTM_ID) {
                TagManager.dataLayer({
                    dataLayer: {
                        event: 'pageview',
                        page: url
                    }
                });
            }
            if (typeof window !== 'undefined' && !!process.env.NEXT_PUBLIC_YM_COUNTER_ID) {
                ym('hit', url);
            }
        }

        router.events.on('routeChangeComplete', handleRouteChange);

        return () => {
            router.events.off('routeChangeComplete', handleRouteChange);
        }
    }, [router]);

    // Use the layout defined at the page level, if available
    const getLayout = Component.getLayout || ((page) => page);

    return (
        <QueryClientProvider client={queryClient}>
            <Hydrate state={pageProps.dehydratedState}>
                <SiteProvider site={site}>
                    <SessionProvider session={session}>
                        <SSRProvider>
                            { getLayout(<Component {...pageProps} />) }
                        </SSRProvider>
                        { !!process.env.NEXT_PUBLIC_YM_COUNTER_ID && (
                            <YMInitializer
                                accounts={[parseInt(process.env.NEXT_PUBLIC_YM_COUNTER_ID)]}
                                options={{
                                    webvisor: true,
                                    defer: true,
                                    clickmap: true,
                                    trackLinks: true,
                                    accurateTrackBounce: true,
                                    ecommerce:"dataLayer"
                                }}
                                version="2" />
                        )}
                    </SessionProvider>
                </SiteProvider>
                <ReactQueryDevtools initialIsOpen={false} />
            </Hydrate>
        </QueryClientProvider>
    );
}
