import { ReactNode } from 'react'
import { Metadata } from 'next/types'
import { Roboto } from 'next/font/google'

import 'swiper/css'
import 'swiper/css/pagination'
import 'yet-another-react-lightbox/styles.css'
import '../styles.scss'

import '@/lib/moment'

import Header from '@/components/layout/header'
import Footer from '@/components/layout/footer'
import { YandexMetrika } from '@/lib/ymec'

import Providers from './providers'

// the variable font covers all weights, as on the old pages
const roboto = Roboto({
  subsets: ['latin', 'cyrillic'],
  variable: '--font-roboto',
})

export const metadata: Metadata = {
  title: {
    template: '%s - Family',
    default: 'Family',
  },
  description: 'Швейные машины и аксессуары Family',
  robots: 'all,follow',
  verification: {
    yandex: [
      '6e328a4eff438f46',
      'f8bbdebb7f2a6f33',
      '9d6d54901642b029',
      '0c2c065329da0681',
      '6462f73cb6863828',
    ],
  },
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // the font variable is set on the root element, Bootstrap's --bs-font-* variables refer to it there
    <html lang="ru" className={roboto.variable}>
      <body>
        <Providers>
          {/* Base UI popups are portalled after it, so they stack on top */}
          <div className="root">
            <Header />
            <main>
              {children}
            </main>
            <Footer />
          </div>
        </Providers>
      </body>
      {process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID && <YandexMetrika
        ymId={process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID}
        trackLinks
        accurateTrackBounce
        webvisor
        clickmap
        ecommerce="dataLayer"
      />}
    </html>
  )
}
