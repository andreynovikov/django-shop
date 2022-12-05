import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Script from 'next/script';
import { QueryClient, QueryClientProvider, Hydrate } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import TagManager from 'react-gtm-module';
import ym, { YMInitializer } from 'react-yandex-metrika';

import { SessionProvider } from '@/lib/session';
import { apiClient, categoryKeys, productKeys, pageKeys } from '@/lib/queries';

import 'tiny-slider/dist/tiny-slider.css';
import 'glightbox/dist/css/glightbox.css';
import '../styles.scss';

export default function App({ Component, pageProps: { session, ...pageProps }}) {
    const router = useRouter();

    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                refetchOnWindowFocus: process.env.NODE_ENV !== 'development',
                retry: process.env.NODE_ENV === 'development' ? 1 : 3
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
                <SessionProvider session={session}>
                    <Script id="bootstrap" src="/js/bootstrap.bundle.js" />
                    { getLayout(<Component {...pageProps} />) }
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
                <ReactQueryDevtools initialIsOpen={false} />
            </Hydrate>
        </QueryClientProvider>
    );
}
