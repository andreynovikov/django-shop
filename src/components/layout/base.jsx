import { useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Script from 'next/script'

import { YandexMetrika } from '@/lib/ymec'

import Favicons from './favicons'
import TopBar from './topbar'
import BottomBar from './bottombar'
import HandheldBottomBar from './handheld-bottombar'
import ScrollTopButton from './scroll-top-button'
import { useTopbar } from '@/lib/topbar'

export default function BaseLayout({
  title,
  description = "Швейный Мир - швейные, вышивальные и вязальные машины, оверлоки и аксессуары",
  htmlTitle = undefined,
  // TODO: restore functionality after full switch to app router
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  hideSignIn = false,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  hideCartNotice = false,
  contentWrapper = ({ children }) => children,
  children,
  ...props
}) {
  const router = useRouter()
  const { setTopMenuOpen } = useTopbar()

  useEffect(() => {
    const handleRouteChange = () => {
      setTopMenuOpen(false)
    }
    router.events.on('routeChangeStart', handleRouteChange)
    return () => {
      router.events.off('routeChangeStart', handleRouteChange)
    }
  }, [router.events, setTopMenuOpen])

  return (
    <>
      <Head>
        <title>{`${(htmlTitle || title) ? (htmlTitle || title) + " - " : ""}Швейный Мир`}</title>
        <meta name="description" content={description} />
        <meta name="keywords" content="швейные машины, вышивальные и вязальные машины, оверлоки и аксессуары во всероссийской сети супермаркетов Швейный Мир, швейная, швейные, вышивальная, вышивальные, вязальная, вязальные, машинка, машина, машинки, машины, оверлок, оверлоки,  шитье, вышивка, вязание, купить, интернет, магазин, pfaff, brother, janome, bernina, husqvarna, huskystar, viking, оверлок, строчка, петля, челнок, стежок, ткань, рукав" />
        <Favicons />
      </Head>
      <div className="root">
        <div className="d-flex flex-column min-vh-100">
          <main className="page-wrapper">
            <TopBar />
            {contentWrapper({ title, children, ...props })}
          </main>

          <BottomBar />
        </div>
        <HandheldBottomBar />
        <ScrollTopButton />
      </div>
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
    </>
  )
}
