import { createContext, useContext, useState, useEffect, useEffectEvent, useRef, ReactNode, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { userKeys, userReferences, userDependencies, currentUser, registerUser, loginUser, logoutUser, isPhoneCodeSent, LoginCredentials, LoginResult, RegistrationData, HttpError } from '@/lib/queries'
import { AnonymousUser, PhoneCodeSent, User } from '@/lib/types';

type LoginResultWithOk = LoginResult & { ok: boolean }
type SignInResult = Promise<LoginResultWithOk | {
  status: number
  error: string | unknown
  ok: boolean
}>

// The new user, signed in, or the code sent to the phone, which the data has to come back with
type RegisterResult = Promise<{ user: User } | { codeSent: PhoneCodeSent } | { error: unknown }>

type SessionStatusType = 'loading' | 'unauthenticated' | 'authenticated'

// What the callers of signOut() show when it returns false
export const SIGN_OUT_FAILED = 'Не удалось выйти, попробуйте ещё раз'

interface SessionContextType {
  user: AnonymousUser | User | undefined
  registered: boolean
  status: SessionStatusType
  signIn: (credentials: LoginCredentials) => SignInResult
  // false when the user is still signed in, the caller tells them
  signOut: (options?: { callbackUrl?: string }) => Promise<boolean>
  register: (data: RegistrationData) => RegisterResult
  invalidate: () => void
}

export const SessionContext = createContext<SessionContextType>({
  user: undefined,
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

  // Callers pass a new callback on each render, calling it again would restart its navigation
  const handleUnauthenticated = useEffectEvent(() => onUnauthenticated?.())

  useEffect(() => {
    if (required)
      handleUnauthenticated()
  }, [required])

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
  const queryClient = useQueryClient()
  const router = useRouter()

  // A user request still in flight was sent before the change and would bring back the old user.
  // Invalidation reuses a first request instead of repeating it, so it is cancelled first.
  // The new user is awaited: until it arrives the old one is in the cache, and a page opened
  // right after signing in would see the visitor as anonymous and send them back to the login page.
  const refreshUser = useCallback(async () => {
    await queryClient.cancelQueries({ queryKey: userKeys.current() })
    await queryClient.invalidateQueries({ queryKey: userKeys.current() })
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

    try {
      await logoutUser()
    } catch (error) {
      console.warn('signOut', error)
    }
    // After a failure the session may have ended or not, the backend tells
    await refreshUser()
    const current = queryClient.getQueryData<AnonymousUser | User>(userKeys.current())
    if ((current?.id ?? 0) > 0)
      return false
    setRegistered(false)
    if (callbackUrl)
      router.push(callbackUrl)
    return true
  }, [queryClient, refreshUser, router])

  const register = useCallback(async (data: RegistrationData) => {
    try {
      const result = await registerUser(data)
      if (isPhoneCodeSent(result))
        return { codeSent: result }
      await refreshUser()
      return { user: result }
    } catch (error) {
      console.log(error)
      return { error }
    }
  }, [refreshUser])

  const invalidate = useCallback(() => {
    setRegistered(false)
    refreshUser()
  }, [refreshUser])

  const { data: user, isSuccess, isLoading } = useQuery({
    queryKey: userKeys.current(),
    queryFn: () => currentUser(),
    staleTime: Infinity,
    refetchOnWindowFocus: 'always',
  })

  // The user the cached data belongs to. The cache starts empty, so the first user found has nothing to reset.
  const userId = user?.id ?? 0
  const dataUserId = useRef<number>(undefined)

  useEffect(() => {
    if (!isLoading) {
      // Signed out, signed in, or another user signed in in another tab: the data of the one before must go
      if (dataUserId.current !== undefined && dataUserId.current !== userId)
        userReferences.map((key) => queryClient.resetQueries({ queryKey: key }))
      dataUserId.current = userId
      userDependencies.map((key) => queryClient.invalidateQueries({ queryKey: key }))
    }
  }, [user, userId, isLoading, queryClient])

  const value = {
    user,
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
