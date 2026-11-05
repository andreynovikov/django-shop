import { cache, ReactNode } from 'react'
import { Metadata } from 'next/types'

import 'yet-another-react-lightbox/styles.css'
import '../styles.scss'

import '@/lib/moment'

import Header from '@/components/layout/header'
import Footer from '@/components/layout/footer'
import { loadCurrentSite } from '@/lib/queries'
import { YandexMetrika } from '@/lib/ymec'

import Providers from './providers'

const getSite = cache(loadCurrentSite)

// Title and description come from the site settings on the backend
export async function generateMetadata(): Promise<Metadata> {
  const site = await getSite()

  return {
    title: {
      template: `%s - ${site.title}`,
      default: site.title,
    },
    description: site.description,
    robots: 'all,follow',
  }
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Providers>
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
