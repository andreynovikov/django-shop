"use client"

import Script from 'next/script'

export type YMParams = {
  ymId: string
  trackHash?: boolean,
  trackLinks?: boolean,
  accurateTrackBounce?: boolean,
  clickmap?: boolean,
  webvisor?: boolean,
  ecommerce?: string
}

declare global {
  interface Window {
    dataLayer?: object[]
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    [key: string]: any
  }
}

export function YandexMetrika(props: YMParams) {
  const { ymId, ...config } = props

  return (
    <>
      <Script
        id="_sw-ym-init"
        dangerouslySetInnerHTML={{
          __html: `
            window['dataLayer'] = window['dataLayer'] || [];
            window['ym'] = window['ym'] || function(){(window['ym'].a=window['ym'].a||[]).push(arguments)};
            window['ym'].l = 1*new Date();
          `,
        }}
      />
      <Script
        id="_sw-ym"
        src="https://mc.yandex.ru/metrika/tag.js"
        onReady={() => {
          window['ym'](ymId, "init", config)
        }}
      />
      <noscript>
        <div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`https://mc.yandex.ru/watch/${ymId}`} style={{ position: "absolute", left: "-9999px" }} alt="" />
        </div>
      </noscript>
    </>
  )
}

export function eCommerce(payload: Record<string, unknown>) {
  if (window['dataLayer'] === undefined) {
    if (process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID)
      console.warn('Yandex metrika is not initialized or Ad blocker is used')
    return
  }

  window['dataLayer'].push({
    ecommerce: {
      currencyCode: "RUB",
    ...payload
    }
  })
}