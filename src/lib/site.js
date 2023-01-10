import { createContext, useContext, useMemo } from 'react';
import { useQuery } from 'react-query';

import { siteKeys, loadCurrentSite } from '@/lib/queries';

export const SiteContext = createContext({status: 'loading', site: {}});

export function useSite() {
    return useContext(SiteContext);
}

export function SiteProvider({children}) {
    const { data: site, isSuccess, isLoading } = useQuery(
        siteKeys.current(),
        () => loadCurrentSite(),
        {
            placeholderData: {},
            cacheTime: 1000 * 60 * 60 * 24, // cache for one day
            staleTime: Infinity,
            refetchOnWindowFocus: false,
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const value = useMemo(() => ({
        site,
        status: isLoading ? 'loading' : isSuccess ? 'success' : 'error'
    }), [site, isLoading, isSuccess]);

    return (
        <SiteContext.Provider value={value}>{children}</SiteContext.Provider>
    )
}
