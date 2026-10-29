import { createContext, useContext, useState, useEffect, useEffectEvent, ReactNode, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { useNavigation } from './navigation';
import { userKeys, userReferences, userDependencies, currentUser, registerUser, loginUser, logoutUser, LoginCredentials, LoginResult, HttpError } from '@/lib/queries'
import { AnonymousUser, User } from '@/lib/types';

type LoginResultWithOk = LoginResult & { ok: boolean }
type SignInResult = Promise<LoginResultWithOk | {
  status: number
  error: string | unknown
  ok: boolean
}>

type RegisterResult = Promise<(User & { ok: boolean }) | {
  error: unknown
}>

type SessionStatusType = 'loading' | 'unauthenticated' | 'authenticated'
interface SessionContextType {
  user: AnonymousUser | User | undefined
  isRouting: boolean
  registered: boolean
  status: SessionStatusType
  signIn: (credentials: LoginCredentials) => SignInResult
  signOut: (options?: { callbackUrl?: string }) => Promise<void>
  register: (data: FormData) => RegisterResult
  invalidate: () => void
}

export const SessionContext = createContext<SessionContextType>({
  user: undefined,
  isRouting: false,
  registered: false,
  status: 'unauthenticated',
  signIn: () => Promise.reject({ status: 'unauthenticated', error: undefined, ok: false }),
  signOut: () => Promise.reject(),
  register: () => Promise.reject({ error: undefined }),
  invalidate: () => { },
})

export function useSession(options?: { onUnauthenticated?: () => void }) {
  const value = useContext(SessionContext)

  const { onUnauthenticated } = options || {}
  const required = onUnauthenticated !== undefined && value.status === 'unauthenticated'

  // Callers pass a new callback on each render. Calling it again would restart its navigation,
  // a full page load when the login page is in the other router.
  const handleUnauthenticated = useEffectEvent(() => onUnauthenticated?.())

  useEffect(() => {
    if (required && !value.isRouting)
      handleUnauthenticated()
  }, [required, value.isRouting])

  return {
    ...value,
    status: required ? 'loading' : value.status
  }
}

interface SessionProviderProps {
  children: ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [registered, setRegistered] = useState(false) // true if user is newly registered
  const [isRouting, setIsRouting] = useState(false)
  const queryClient = useQueryClient()
  const { navigate, events } = useNavigation()

  // A user request still in flight was sent before the change and would bring back the old user.
  // Invalidation reuses a first request instead of repeating it, so it is cancelled first.
  const refreshUser = useCallback(async () => {
    await queryClient.cancelQueries({ queryKey: userKeys.current() })
    queryClient.invalidateQueries({ queryKey: userKeys.current() })
  }, [queryClient])

  const signIn = useCallback(async (credentials: LoginCredentials) => {
    try {
      const user = await loginUser(credentials)
      setRegistered(user.registered)
      return {
        ...user,
        ok: +user.id > 0
      }
    } catch (error) {
      console.log("signIn", error)
      return {
        status: error instanceof HttpError ? error.response.status : 500,
        error: error instanceof HttpError ? await error.response.text() : error,
        ok: false
      }
    } finally {
      await refreshUser()
    }
  }, [refreshUser])

  const signOut = useCallback(async (options?: { callbackUrl?: string }) => {
    const { callbackUrl } = options || {}

    await logoutUser()
    setRegistered(false)
    await refreshUser()
    if (callbackUrl)
      navigate(callbackUrl)
  }, [refreshUser, navigate])

  const register = useCallback(async (data: FormData) => {
    try {
      const result = await registerUser(data)
      return {
        ...result,
        ok: +result.id > 0
      }
    } catch (error) {
      console.log(error)
      return {
        error
      }
    } finally {
      await refreshUser()
    }
  }, [refreshUser])

  const invalidate = useCallback(() => {
    setRegistered(false)
    refreshUser()
  }, [refreshUser])

  const handleRouteChangeStart = () => setIsRouting(true)
  const handleRouteChangeComplete = () => setIsRouting(false)

  useEffect(() => {
    if (events === undefined)
      return

    events.on('routeChangeStart', handleRouteChangeStart)
    events.on('routeChangeComplete', handleRouteChangeComplete)

    return () => {
      events.off('routeChangeStart', handleRouteChangeStart)
      events.off('routeChangeComplete', handleRouteChangeComplete)
    }
  }, [events])

  const { data: user, isSuccess, isLoading } = useQuery({
    queryKey: userKeys.current(),
    queryFn: () => currentUser(),
    staleTime: Infinity,
    refetchOnWindowFocus: 'always',
  })

  useEffect(() => {
    console.log("SessionProvider", user?.id, "isLoading", isLoading)
    if (!isLoading) {
      if ((user?.id ?? 0) === 0)
        userReferences.map((key) => queryClient.resetQueries({ queryKey: key }))
      userDependencies.map((key) => queryClient.invalidateQueries({ queryKey: key }))
    }
  }, [user, isLoading, queryClient])

  const value = {
    user,
    isRouting,
    registered,
    status: (isLoading ? 'loading' : isSuccess && (user?.id ?? 0) > 0 ? 'authenticated' : 'unauthenticated') as SessionStatusType,
    signIn,
    signOut,
    register,
    invalidate,
  }
  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  )
}
