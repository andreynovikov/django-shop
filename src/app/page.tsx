import Link from 'next/link'

import { ParallaxProvider, ParallaxBanner, ParallaxBannerLayer } from '@/components/home/parallax'
import NewsCarousel from '@/components/home/news-carousel'
import ReviewsCarousel from '@/components/home/reviews-carousel'

import { loadPromoReviews, loadNews } from '@/lib/queries'

// News and reviews have no revalidation of their own on this page
export const revalidate = 3600

export default async function IndexPage() {
  const [news, reviews] = await Promise.all([loadNews(), loadPromoReviews()])

  return (
    <ParallaxProvider>
      <ParallaxBanner className="vh-100 d-flex align-items-center">
        <ParallaxBannerLayer image="/i/photo/sm.jpg" expanded={false} speed={-20} className="sw-bg-right opacity-75" />
        <div className="container py-5 overflow-hidden overlay-content mx-auto text-center">
          <h1 className="mb-5 display-4 fw-bold text-uppercase">
            <Link className="text-dark text-decoration-none" href="/catalog/sewing_machines/">
              Швейные машины
            </Link>
          </h1>
          <Link className="btn btn-dark" href="/catalog/sewing_machines/">Большой выбор в каталоге</Link>
        </div>
      </ParallaxBanner>
      <div className="container py-5 py-sm-6">
        <div className="row">
          <div className="col-lg-8 mx-auto">
            <NewsCarousel news={news} />
            <div className="mt-4 text-end">
              <Link className="btn btn-dark" href="/news/">Другие новости</Link>
            </div>
          </div>
        </div>
      </div>
      <ParallaxBanner className="vh-100 d-flex align-items-center">
        <ParallaxBannerLayer image="/i/photo/acc.jpg" expanded={false} speed={-20} className="opacity-25" />
        <div className="container py-5 overflow-hidden overlay-content mx-auto text-center">
          <h1 className="mb-3 display-4 fw-bold text-uppercase">Обзор машин серии Gold Master</h1>
          <div className="ratio ratio-16x9">
            <iframe
              src="https://www.youtube.com/embed/7csbLjVYw68"
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen />
          </div>
        </div>
      </ParallaxBanner>
      <ParallaxBanner className="vh-100 d-flex align-items-center">
        <ParallaxBannerLayer image="/i/photo/ov.jpg" expanded={false} speed={-20} className="sw-bg-right opacity-75" />
        <div className="container py-5 overflow-hidden overlay-content mx-auto text-start">
          <h1 className="mb-3 display-4 fw-bold text-uppercase">
            <Link className="text-dark text-decoration-none" href="/catalog/overlock/">
              Оверлоки,<br /> коверлоки<br /> и плоскошовные<br /> машины
            </Link>
          </h1>
          <Link className="btn btn-dark" href="/catalog/overlock/">Выберите модель</Link>
        </div>
      </ParallaxBanner>
      {reviews.results.length > 0 && (
        <div className="container py-5 py-sm-6">
          <div className="row">
            <div className="col-lg-8 mx-auto">
              <ReviewsCarousel reviews={reviews.results} />
            </div>
          </div>
        </div>
      )}
      <ParallaxBanner className="vh-100 d-flex align-items-center text-dark">
        <ParallaxBannerLayer image="/i/photo/acc.jpg" expanded={false} speed={-20} className="opacity-75" />
        <div className="container py-5 overflow-hidden overlay-content mx-auto text-start">
          <h1 className="mb-3 display-4 fw-bold text-uppercase">
            <Link className="text-dark text-decoration-none" href="/catalog/accessories/">
              Аксессуары
            </Link>
          </h1>
          <p className="display-6 mb-5">Коллекция самых полезных товаров<br /> для шитья и рукоделия</p>
          <Link className="btn btn-dark" href="/catalog/accessories/">Посмотрите каталог</Link>
        </div>
      </ParallaxBanner>
    </ParallaxProvider>
  )
}
