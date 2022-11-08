import { createContext, useContext, useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from 'react-query';

import { apiClient, userKeys, currentUser } from '@/lib/queries';

export const SessionContext = createContext(undefined);

const __SESSION = {
    _invalidate: () => {}
};

export function useSession(options) {
    const value = useContext(SessionContext);

    const { onUnauthenticated } = options || {};
    const requiredAndNotLoading = onUnauthenticated !== undefined && value.status === 'unauthenticated';

    useEffect(() => {
        if (requiredAndNotLoading)
            onUnauthenticated();
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [requiredAndNotLoading]);

    if (requiredAndNotLoading)
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
                router.push(callbackUrl);
        });
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
        status: isLoading ? 'loading'
            : isSuccess && user?.id > 0 ? 'authenticated'
            : 'unauthenticated'
    }), [user, isLoading, isSuccess]);

    return (
        <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
    )
}
