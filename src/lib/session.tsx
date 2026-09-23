import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { useRouter } from 'next/router'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { userKeys, userReferences, userDependencies, currentUser, registerUser, loginUser, logoutUser, LoginCredentials, LoginResult, HttpError } from '@/lib/queries'
import { AnonymousUser, User } from '@/lib/types';

type LoginResultWithOk = LoginResult & { ok: boolean }
type SignInResult = Promise<LoginResultWithOk | {
  status: number
  error: string | unknown
  ok: boolean
}>

type RegisterResult = Promise<User | {
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

  useEffect(() => {
    if (required && !value.isRouting)
      onUnauthenticated()
  }, [onUnauthenticated, required, value.isRouting])

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
  const router = useRouter()
  const queryClient = useQueryClient()

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
      queryClient.invalidateQueries({ queryKey: userKeys.current() })
    }
  }, [queryClient])

  const signOut = useCallback(async (options?: { callbackUrl?: string }) => {
    const { callbackUrl } = options || {}

    await logoutUser()
    setRegistered(false)
    queryClient.invalidateQueries({ queryKey: userKeys.current() })
    if (callbackUrl)
      router.push(callbackUrl)
  }, [queryClient, router])

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
      queryClient.invalidateQueries({ queryKey: userKeys.current() })
    }
  }, [queryClient])

  const invalidate = useCallback(() => {
    setRegistered(false)
    queryClient.invalidateQueries({ queryKey: userKeys.current() })
  }, [queryClient])

  const handleRouteChangeStart = () => setIsRouting(true)
  const handleRouteChangeComplete = () => setIsRouting(false)

  useEffect(() => {
    router.events.on('routeChangeStart', handleRouteChangeStart)
    router.events.on('routeChangeComplete', handleRouteChangeComplete)

    return () => {
      router.events.off('routeChangeStart', handleRouteChangeStart)
      router.events.off('routeChangeComplete', handleRouteChangeComplete)
    }
  }, [router.events])

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
