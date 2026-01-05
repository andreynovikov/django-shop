import { createContext, useContext, useState, useEffect, useMemo } from 'react'
import Router, { useRouter } from 'next/router'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, userKeys, userReferences, userDependencies, currentUser } from '@/lib/queries'

export const SessionContext = createContext({
  user: undefined,
  isRouting: false,
  registered: false,
  status: 'unauthenticated'
})

const __SESSION = {
  invalidate: () => { },
  registered: false
}

export function useSession(options) {
  const value = useContext(SessionContext)

  const { onUnauthenticated } = options || {}
  const required = onUnauthenticated !== undefined && value.status === 'unauthenticated'

  useEffect(() => {
    if (required && !value.isRouting)
      onUnauthenticated()
  }, [onUnauthenticated, required, value.isRouting])

  if (required)
    return { user: value.user, status: 'loading' }

  return value
}

export async function signIn(credentials) {
  return apiClient.post('users/login/', credentials)
    .then(function (response) {
      __SESSION.registered = response.data.registered
      return {
        ...response.data,
        ok: +response.data.id > 0
      }
    })
    .catch(function (error) {
      // handle error
      console.log("signIn", error)
      return {
        error: error.response?.data ?? error.message,
        ok: false
      }
    })
    .then(function (result) {
      __SESSION.invalidate()
      return result
    })
}

export async function signOut(options) {
  const { callbackUrl } = options || {}

  return apiClient.get('users/logout/')
    .then(function () {
      __SESSION.registered = false
      __SESSION.invalidate()
      if (callbackUrl)
        Router.push(callbackUrl)
    })
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
      console.log(error)
      return {
        error
      }
    })
    .then(function (result) {
      __SESSION.invalidate()
      return result
    })
}

export function invalidate() {
    __SESSION.registered = false;
    __SESSION.invalidate();
}

export function SessionProvider({ children }) {
  const [isRouting, setIsRouting] = useState(false)
  const router = useRouter()
  const queryClient = useQueryClient()

  const handleRouteChangeStart = () => setIsRouting(true)
  const handleRouteChangeComplete = () => setIsRouting(false)

  useEffect(() => {
    __SESSION.invalidate = () => {
      queryClient.invalidateQueries({ queryKey: userKeys.current() })
    }

    router.events.on('routeChangeStart', handleRouteChangeStart)
    router.events.on('routeChangeComplete', handleRouteChangeComplete)

    return () => {
      __SESSION.invalidate = () => { }
      router.events.off('routeChangeStart', handleRouteChangeStart)
      router.events.off('routeChangeComplete', handleRouteChangeComplete)
    }
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [])

  const { data: user, isSuccess, isLoading } = useQuery({
    queryKey: userKeys.current(),
    queryFn: () => currentUser(),
    staleTime: Infinity,
    refetchOnWindowFocus: 'always',
  })

  useEffect(() => {
    console.log("SessionProvider", user?.id, "isLoading", isLoading)
    if (!isLoading) {
      if (!(user?.id > 0))
        userReferences.map((key) => queryClient.resetQueries({ queryKey: key }))
      userDependencies.map((key) => queryClient.invalidateQueries({ queryKey: key }))
    }
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [user, isLoading])

  const value = useMemo(() => ({
    user,
    isRouting,
    registered: __SESSION.registered,
    status: isLoading ? 'loading'
      : isSuccess && user?.id > 0 ? 'authenticated'
        : 'unauthenticated'
  }), [user, isLoading, isSuccess], isRouting, __SESSION.registered)

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  )
}
