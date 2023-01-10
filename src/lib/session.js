import { createContext, useContext, useEffect, useMemo } from 'react';
import Router from 'next/router';
import { useQuery, useQueryClient } from 'react-query';

import { apiClient, userKeys, currentUser } from '@/lib/queries';

export const SessionContext = createContext(undefined);

const __SESSION = {
    _invalidate: () => {},
    registered: false,
    routeChanging: false
};

export function useSession(options) {
    const value = useContext(SessionContext);

    const { onUnauthenticated } = options || {};
    const requiredAndNotLoading = onUnauthenticated !== undefined && value.status === 'unauthenticated';
    //console.log("useSession", requiredAndNotLoading, onUnauthenticated, value);

    useEffect(() => {
        const handleRouteChangeStart = () => {
            __SESSION.routeChanging = true;
        };
        const handleRouteChangeComplete = () => {
            __SESSION.routeChanging = false;
        };

        Router.events.on('routeChangeStart', handleRouteChangeStart);
        Router.events.on('routeChangeComplete', handleRouteChangeComplete);

        return () => {
            Router.events.off('routeChangeStart', handleRouteChangeStart);
            Router.events.off('routeChangeComplete', handleRouteChangeComplete);
        }
    }, []);

    useEffect(() => {
        if (requiredAndNotLoading && !__SESSION.routeChanging)
            onUnauthenticated();
    }, [onUnauthenticated, requiredAndNotLoading]);

    if (requiredAndNotLoading)
        return { ...value, status: 'loading' };

    return value;
}

export async function signIn(credentials) {
    return apiClient.post('users/login/', credentials)
        .then(function (response) {
            __SESSION.registered = response.data.registered;
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
            __SESSION.registered = false;
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

export function invalidate() {
    __SESSION.registered = false;
    __SESSION.invalidate();
}

export function SessionProvider({children}) {
    const queryClient = useQueryClient();

    useEffect(() => {
        __SESSION.invalidate = () => {
            queryClient.invalidateQueries(userKeys.current());
        }

        return () => {
            __SESSION.invalidate = () => {}
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
                queryClient.resetQueries(userKeys.references());
            queryClient.invalidateQueries(userKeys.dependencies());
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [user, isLoading]);

    const value = useMemo(() => ({
        user,
        registered: __SESSION.registered,
        status: isLoading ? 'loading'
            : isSuccess && user?.id > 0 ? 'authenticated'
            : 'unauthenticated'
    }), [user, isLoading, isSuccess, __SESSION.registered]);

    return (
        <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
    )
}
