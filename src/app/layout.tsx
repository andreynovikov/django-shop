import { ReactNode } from 'react'
import { Metadata } from 'next/types'
import Script from 'next/script'
import localFont from 'next/font/local'

import 'simplebar-react/dist/simplebar.min.css'
import 'swiper/css'
import 'swiper/css/free-mode'
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import '../styles.scss'

import '@/lib/moment'

import Catalog from '@/components/catalog'
import TopBar from '@/components/layout/topbar'
import BottomBar from '@/components/layout/bottombar'
import HandheldBottomBar from '@/components/layout/handheld-bottombar'
import ScrollTopButton from '@/components/layout/scroll-top-button'
import { loadCategories } from '@/lib/queries'
import { YandexMetrika } from '@/lib/ymec'

import Providers from './providers'

const rubik = localFont({
  src: [
    {
      path: '../assets/fonts/Rubik/Rubik-VariableFont_wght.ttf',
      style: 'normal',
    }, {
      path: '../assets/fonts/Rubik/Rubik-Italic-VariableFont_wght.ttf',
      style: 'italic',
    }
  ],
  fallback: ['sans-serif'],
  variable: '--font-rubik',
})

export const metadata: Metadata = {
  title: {
    template: '%s - Швейный Мир',
    default: 'Швейный Мир',
  },
  description: 'Швейный Мир - швейные, вышивальные и вязальные машины, оверлоки и аксессуары',
  keywords: 'швейные машины, вышивальные и вязальные машины, оверлоки и аксессуары во всероссийской сети супермаркетов Швейный Мир, швейная, швейные, вышивальная, вышивальные, вязальная, вязальные, машинка, машина, машинки, машины, оверлок, оверлоки,  шитье, вышивка, вязание, купить, интернет, магазин, pfaff, brother, janome, bernina, husqvarna, huskystar, viking, оверлок, строчка, петля, челнок, стежок, ткань, рукав',
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION,
    yandex: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION,
  },
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const categories = await loadCategories()

  return (
    <html lang="ru">
      <body className={rubik.variable}>
        <Providers>
          <div className="root">
            <div className="d-flex flex-column min-vh-100">
              <main className="page-wrapper">
                <TopBar catalog={<Catalog categories={categories} />} />
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
