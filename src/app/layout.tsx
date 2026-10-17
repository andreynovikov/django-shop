import { ReactNode } from 'react'
import Script from 'next/script'
import localFont from 'next/font/local'

import 'simplebar-react/dist/simplebar.min.css'
import 'react-bootstrap-typeahead/css/Typeahead.css'
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css'
import 'swiper/css'
import 'swiper/css/free-mode'
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import '../styles.scss'

import moment, { type MomentInput, type Moment } from 'moment'
import 'moment/locale/ru'

import TopBar from '@/components/layout/topbar'
import BottomBar from '@/components/layout/bottombar'
import HandheldBottomBar from '@/components/layout/handheld-bottombar'
import ScrollTopButton from '@/components/layout/scroll-top-button'
import { YandexMetrika } from '@/lib/ymec'

import Providers from './providers'

moment.locale('ru');
moment.updateLocale('ru', {
  monthsShort: {
    format: 'янв_фев_мар_апр_мая_июн_июл_авг_сен_окт_ноя_дек'.split('_'),
    standalone: 'янв_фев_март_апр_май_июнь_июль_авг_сен_окт_ноя_дек'.split('_')
  },
  calendar: {
    lastWeek: function (m?: MomentInput, now?: Moment) {
      if (now?.week() !== (this as unknown as Moment).week()) {
        switch ((this as unknown as Moment).day()) {
          case 0:
            return '[В прошлое] dddd';
          case 1:
          case 2:
          case 4:
            return '[В прошлый] dddd';
          case 3:
          case 5:
          case 6:
            return '[В прошлую] dddd';
          default:
            return '[В прошлое] dddd';
        }
      } else {
        if ((this as unknown as Moment).day() === 2) {
          return '[Во] dddd';
        } else {
          return '[В] dddd';
        }
      }
    }
  },
});

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

export const metadata = {
  title: {
    template: '%s - Швейный Мир',
    default: 'Швейный Мир',
  },
  description: 'Швейный Мир - швейные, вышивальные и вязальные машины, оверлоки и аксессуары',
  keywords: 'швейные машины, вышивальные и вязальные машины, оверлоки и аксессуары во всероссийской сети супермаркетов Швейный Мир, швейная, швейные, вышивальная, вышивальные, вязальная, вязальные, машинка, машина, машинки, машины, оверлок, оверлоки,  шитье, вышивка, вязание, купить, интернет, магазин, pfaff, brother, janome, bernina, husqvarna, huskystar, viking, оверлок, строчка, петля, челнок, стежок, ткань, рукав',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body className={rubik.variable}>
        <Providers>
          <div className="root">
            <div className="d-flex flex-column min-vh-100">
              <main className="page-wrapper">
                <TopBar />
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
