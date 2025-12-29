import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { QueryClient, QueryClientProvider, HydrationBoundary } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import ym, { YMInitializer } from 'react-yandex-metrika';

import { SiteProvider } from '@/lib/site';
import { SessionProvider } from '@/lib/session';
import { apiClient, categoryKeys, productKeys, pageKeys } from '@/lib/queries';

import 'yet-another-react-lightbox/styles.css';
import '../styles.scss';

export default function App({ Component, pageProps: { site, session, ...pageProps }}) {
    const router = useRouter();

    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                refetchOnWindowFocus: process.env.NODE_ENV !== "development",
                retry: (failureCount, error) => {
                    if (error.request.status === 404)
                        return false;
                    else
                        return failureCount < (process.env.NODE_ENV === "development" ? 1 : 3);
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
        if (!!process.env.NEXT_PUBLIC_YM_COUNTER_ID) {
            ym('hit', router.asPath);
        }
    }, []);

    useEffect(() => {
        const handleRouteChange = (url) => {
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
            <HydrationBoundary state={pageProps.dehydratedState}>
                <SiteProvider site={site}>
                    <SessionProvider session={session}>
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
                </SiteProvider>
            </HydrationBoundary>
            <ReactQueryDevtools />
        </QueryClientProvider>
    );
}
