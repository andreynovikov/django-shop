import { environmentManager, QueryClient } from '@tanstack/react-query'

import { categoryKeys, productKeys, pageKeys } from '@/lib/queries'

type QueryClientOptions = {
  staleTime?: number
}

export function makeQueryClient({ staleTime }: QueryClientOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: process.env.NODE_ENV !== 'development',
        retry: process.env.NODE_ENV === 'development' ? 1 : 5,
        staleTime,
      },
    },
  })

  queryClient.setQueryDefaults(categoryKeys.all, { staleTime: Infinity }) // mark fresh forever
  queryClient.setQueryDefaults(productKeys.all, { staleTime: 1000 * 60 * 10 }) // mark fresh for ten minutes
  queryClient.setQueryDefaults(pageKeys.all, { staleTime: Infinity }) // mark fresh forever

  return queryClient
}

let browserQueryClient: QueryClient | undefined = undefined

// App router client: new instance per server request, singleton in browser
export function getQueryClient() {
  // With SSR, we usually want to set some default staleTime
  // above 0 to avoid refetching immediately on the client
  const options = { staleTime: 60 * 1000 }

  if (environmentManager.isServer()) {
    // Server: always make a new query client
    return makeQueryClient(options)
  } else {
    // Browser: make a new query client if we don't already have one
    // This is very important, so we don't re-make a new client if React
    // suspends during the initial render. This may not be needed if we
    // have a suspense boundary BELOW the creation of the query client
    if (!browserQueryClient) browserQueryClient = makeQueryClient(options)
    return browserQueryClient
  }
}
