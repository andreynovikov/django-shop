import { cache, ReactNode } from 'react'
import { Metadata } from 'next/types'

import 'yet-another-react-lightbox/styles.css'
import '../styles.css'

import '@/lib/moment'

import Header from '@/components/layout/header'
import Footer from '@/components/layout/footer'
import { loadCurrentSite } from '@/lib/queries'
import { YandexMetrika } from '@/lib/ymec'

import Providers from './providers'

const getSite = cache(loadCurrentSite)

// Pages show their own title only, the description comes from the site settings on the backend
export async function generateMetadata(): Promise<Metadata> {
  const site = await getSite()

  return {
    title: {
      template: '%s',
      default: 'Дор Так - Швейные нитки оптом и в розницу',
    },
    description: site.description || '',
    robots: 'all,follow',
    verification: {
      yandex: ['9067b839ade4914a', 'ffa29a305777f97e'],
    },
    icons: {
      icon: { url: '/images/favicon.png', type: 'image/png' },
    },
  }
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Providers>
          {/* Base UI popups are portalled after it, so they stack on top */}
          <div className="isolate">
            <Header />
            <main className="my-6">
              {children}
            </main>
            <Footer />
          </div>
        </Providers>
      </body>
      {process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID && <YandexMetrika
        ymId={process.env.NEXT_PUBLIC_YANDEX_METRIKA_ID}
        webvisor
        clickmap
        trackLinks
        accurateTrackBounce
        ecommerce="dataLayer"
      />}
    </html>
  )
}
