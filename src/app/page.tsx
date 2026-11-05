import Link from 'next/link'

import { buttonClass } from '@/components/ui/button'
import { ParallaxProvider, ParallaxBanner, ParallaxBannerLayer } from '@/components/home/parallax'
import NewsCarousel from '@/components/home/news-carousel'
import ReviewsCarousel from '@/components/home/reviews-carousel'

import { loadPromoReviews, loadNews } from '@/lib/queries'

// News and reviews have no revalidation of their own on this page
export const revalidate = 3600

const bannerClass = 'flex h-screen items-center'
const bannerContentClass = 'container relative z-20 overflow-hidden py-12'
const bannerTitleClass = 'text-4xl leading-[1.1] font-bold tracking-widest uppercase lg:text-6xl'
const bannerTitleLinkClass = 'text-dark hover:no-underline'
const sectionClass = 'container py-12 sm:py-24'

export default async function IndexPage() {
  const [news, reviews] = await Promise.all([loadNews(), loadPromoReviews()])

  return (
    <ParallaxProvider>
      <ParallaxBanner className={bannerClass}>
        <ParallaxBannerLayer image="/i/photo/sm.jpg" expanded={false} speed={-20} className="bg-right! opacity-75" />
        <div className={`${bannerContentClass} text-center`}>
          <h1 className={`mb-12 ${bannerTitleClass}`}>
            <Link className={bannerTitleLinkClass} href="/catalog/sewing_machines/">
              Швейные машины
            </Link>
          </h1>
          <Link className={buttonClass()} href="/catalog/sewing_machines/">Большой выбор в каталоге</Link>
        </div>
      </ParallaxBanner>
      <div className={sectionClass}>
        <div className="lg:mx-auto lg:w-2/3">
          <NewsCarousel news={news} />
          <div className="mt-6 text-end">
            <Link className={buttonClass()} href="/news/">Другие новости</Link>
          </div>
        </div>
      </div>
      <ParallaxBanner className={bannerClass}>
        <ParallaxBannerLayer image="/i/photo/acc.jpg" expanded={false} speed={-20} className="opacity-25" />
        <div className={`${bannerContentClass} text-center`}>
          <h1 className={`mb-4 ${bannerTitleClass}`}>Обзор машин серии Gold Master</h1>
          <div className="aspect-video">
            <iframe
              className="size-full"
              src="https://www.youtube.com/embed/7csbLjVYw68"
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen />
          </div>
        </div>
      </ParallaxBanner>
      <ParallaxBanner className={bannerClass}>
        <ParallaxBannerLayer image="/i/photo/ov.jpg" expanded={false} speed={-20} className="bg-right! opacity-75" />
        <div className={bannerContentClass}>
          <h1 className={`mb-4 ${bannerTitleClass}`}>
            <Link className={bannerTitleLinkClass} href="/catalog/overlock/">
              Оверлоки,<br /> коверлоки<br /> и плоскошовные<br /> машины
            </Link>
          </h1>
          <Link className={buttonClass()} href="/catalog/overlock/">Выберите модель</Link>
        </div>
      </ParallaxBanner>
      {reviews.results.length > 0 && (
        <div className={sectionClass}>
          <div className="lg:mx-auto lg:w-2/3">
            <ReviewsCarousel reviews={reviews.results} />
          </div>
        </div>
      )}
      <ParallaxBanner className={`${bannerClass} text-dark`}>
        <ParallaxBannerLayer image="/i/photo/acc.jpg" expanded={false} speed={-20} className="opacity-75" />
        <div className={bannerContentClass}>
          <h1 className={`mb-4 ${bannerTitleClass}`}>
            <Link className={bannerTitleLinkClass} href="/catalog/accessories/">
              Аксессуары
            </Link>
          </h1>
          <p className="mb-12 text-3xl leading-[1.1] lg:text-4xl">Коллекция самых полезных товаров<br /> для шитья и рукоделия</p>
          <Link className={buttonClass()} href="/catalog/accessories/">Посмотрите каталог</Link>
        </div>
      </ParallaxBanner>
    </ParallaxProvider>
  )
}
