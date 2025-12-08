"use client"

declare const window: Window & {
  dataLayer: Record<string, unknown>[]
}

export function eCommerce(payload: Record<string, any>) {
  if (typeof window === 'undefined') {
    console.warn("No window object")
    return
  }
  window['dataLayer'] = window['dataLayer'] || []
  window['dataLayer'].push(payload)
}