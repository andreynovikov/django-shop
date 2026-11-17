import { lazy, type ComponentType } from 'react'

const RELOAD_KEY = 'lazyReloadAt'
const RELOAD_INTERVAL = 60_000

/**
 * `React.lazy()` that reloads the page when the component's code fails to load.
 *
 * A deploy deletes the previous build's files. In a tab opened before it, client navigation recovers by itself (the
 * router reloads the page when the server's build differs), but a component loaded later, when it is first shown,
 * asks for a file that no longer exists. The reload brings the new build. If the code fails again within a minute
 * of a reload, the error goes to the error boundary instead, so a file that is really broken doesn't reload the
 * page over and over. Without session storage there is no such guard, so there is no reload either.
 */
export function lazyWithReload<P extends object>(load: () => Promise<{ default: ComponentType<P> }>) {
  return lazy(() => load().catch((error: unknown) => {
    try {
      if (Date.now() - Number(sessionStorage.getItem(RELOAD_KEY)) < RELOAD_INTERVAL)
        throw error
      sessionStorage.setItem(RELOAD_KEY, String(Date.now()))
    } catch {
      throw error
    }
    window.location.reload()
    return new Promise<never>(() => {}) // keep showing the Suspense fallback until the page unloads
  }))
}
