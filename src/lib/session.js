import { createContext, useContext, useState, useEffect, useMemo } from 'react';
import Router, { useRouter } from 'next/router';
import { useQuery, useQueryClient } from 'react-query';

import { apiClient, userKeys, userReferences, userDependencies, currentUser } from '@/lib/queries';

export const SessionContext = createContext(undefined);

const __SESSION = {
    _invalidate: () => {}
};

export function useSession(options) {
    const value = useContext(SessionContext);

    const { onUnauthenticated } = options || {};
    const required = onUnauthenticated !== undefined && value.status === 'unauthenticated';

    useEffect(() => {
        if (required && !value.isRouting)
            onUnauthenticated();
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [required, value.isRouting]);

    if (required)
        return { user: value.user, status: 'loading' };

    return value;
}

export async function signIn(credentials) {
    return apiClient.post('users/login/', credentials)
        .then(function (response) {
            return {
                ...response.data,
                ok: +response.data.id > 0
            }
        })
        .catch(function (error) {
            // handle error
            console.log(error);
            return {
                error
            }
        })
        .then(function (result) {
            __SESSION.invalidate();
            return result;
        });
}

export async function signOut(options) {
    const { callbackUrl } = options || {};

    return apiClient.get('users/logout/')
        .then(function () {
            __SESSION.invalidate();
            if (callbackUrl)
                Router.push(callbackUrl);
        });
}

export async function register(data) {
    return apiClient.post('users/', data)
        .then(function (response) {
            return {
                ...response.data,
                ok: +response.data.id > 0
            }
        })
        .catch(function (error) {
            // handle error
            console.log(error);
            return {
                error
            }
        })
        .then(function (result) {
            __SESSION.invalidate();
            return result;
        });
}

export function SessionProvider({children}) {
    const [isRouting, setIsRouting] = useState(false);
    const router = useRouter();
    const queryClient = useQueryClient();

    const handleRouteChangeStart = () => setIsRouting(true);
    const handleRouteChangeComplete = () => setIsRouting(false);

    useEffect(() => {
        __SESSION.invalidate = () => {
            queryClient.invalidateQueries(userKeys.current());
        }

        router.events.on('routeChangeStart', handleRouteChangeStart);
        router.events.on('routeChangeComplete', handleRouteChangeComplete);

        return () => {
            __SESSION.invalidate = () => {};
            router.events.off('routeChangeStart', handleRouteChangeStart);
            router.events.off('routeChangeComplete', handleRouteChangeComplete);
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, []);

    const { data: user, isSuccess, isLoading } = useQuery(
        userKeys.current(),
        () => currentUser(),
        {
            cacheTime: 1000 * 60 * 60, // cache for one hour
            staleTime: Infinity,
            refetchOnWindowFocus: 'always',
            onError: (error) => {
                console.log(error);
            }
        }
    );

    useEffect(() => {
        console.log("SessionProvider", user?.id, "isLoading", isLoading);
        if (!isLoading) {
            if (!(user?.id > 0))
                userReferences.map((keys) => queryClient.resetQueries(keys));
            userDependencies.map((keys) => queryClient.invalidateQueries(keys));
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [user, isLoading]);

    const value = useMemo(() => ({
        user,
        isRouting,
        status: isLoading ? 'loading'
            : isSuccess && user?.id > 0 ? 'authenticated'
            : 'unauthenticated'
    }), [user, isLoading, isSuccess], isRouting);

    return (
        <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
    )
}
