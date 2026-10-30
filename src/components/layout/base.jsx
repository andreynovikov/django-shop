import { useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Script from 'next/script'
import { useQuery } from '@tanstack/react-query'

import { YandexMetrika } from '@/lib/ymec'

import Catalog from '@/components/catalog'
import { categoryKeys, loadCategories } from '@/lib/queries'

import Favicons from './favicons'
import TopBar from './topbar'
import BottomBar from './bottombar'
import HandheldBottomBar from './handheld-bottombar'
import ScrollTopButton from './scroll-top-button'
import { useTopbar } from '@/lib/topbar'

export default function BaseLayout({
  title,
  description = "Janome - швейные машины, вышивальные машины, оверлоки и аксессуары",
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

  // Pages Router can't render server components, so the catalog is loaded here until the pages move to App Router
  const { data: categories } = useQuery({
    queryKey: categoryKeys.lists(),
    queryFn: () => loadCategories()
  })

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
        <title>{`${(htmlTitle || title) ? (htmlTitle || title) + " - " : ""}Janome.Club`}</title>
        <meta name="description" content={description} />
        <meta name="keywords" content="швейные машины, вышивальные машины, оверлоки и аксессуары Janome" />
        <Favicons />
      </Head>
      <div className="root">
        <div className="d-flex flex-column min-vh-100">
          <main className="page-wrapper">
            <TopBar catalog={categories && <Catalog categories={categories} />} />
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
