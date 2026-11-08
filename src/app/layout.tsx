import { ReactNode } from 'react'
import { Metadata } from 'next/types'
import Script from 'next/script'

import 'swiper/css'
import 'swiper/css/free-mode'
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import '../styles.css'

import '@/lib/moment'

import Catalog from '@/components/catalog'
import TopBar from '@/components/layout/topbar'
import BottomBar from '@/components/layout/bottombar'
import HandheldBottomBar from '@/components/layout/handheld-bottombar'
import ScrollTopButton from '@/components/layout/scroll-top-button'
import { loadCategories } from '@/lib/queries'
import { YandexMetrika } from '@/lib/ymec'

import Providers from './providers'

export const metadata: Metadata = {
  title: {
    template: '%s - Janome.Club',
    default: 'Janome.Club',
  },
  description: 'Janome - швейные машины, вышивальные машины, оверлоки и аксессуары',
  keywords: 'швейные машины, вышивальные машины, оверлоки и аксессуары Janome',
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION,
    yandex: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION,
  },
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const categories = await loadCategories()

  return (
    <html lang="ru" className="has-[.sw-no-body-scroll]:overflow-hidden">
      <body>
        <Providers>
          <div className="isolate">
            <div className="flex min-h-screen flex-col">
              <TopBar catalog={<Catalog categories={categories} />} />
              <main className="flex-auto">
                {children}
              </main>
              <BottomBar />
            </div>
            <HandheldBottomBar />
            <ScrollTopButton />
          </div>
        </Providers>
      </body>
      {process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID && <YandexMetrika
        ymId={process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID}
        trackHash
        trackLinks
        accurateTrackBounce
        webvisor
        clickmap
        ecommerce="dataLayer"
      />}
      {process.env.NEXT_PUBLIC_JIVO_KEY && <Script src={"https://code.jivo.ru/widget/" + process.env.NEXT_PUBLIC_JIVO_KEY} strategy="lazyOnload" />}
    </html>
  )
}
