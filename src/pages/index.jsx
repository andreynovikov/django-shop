import { useState, useEffect } from 'react';
import Link from 'next/link';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import { ParallaxProvider, ParallaxBanner, ParallaxBannerLayer } from 'react-scroll-parallax';

import Layout from '@/components/layout';
import ReviewItem from '@/components/review/item';

import { reviewKeys, loadPromoReviews, newsKeys, loadNews } from '@/lib/queries';

import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function Index() {
    const [tnsModule, setTnsModule] = useState(null);

    useEffect(() => {
        import('tiny-slider').then((module) => {
            setTnsModule(module);
        });
    }, []);

    const { data: reviews, isSuccess: isReviewSuccess } = useQuery(reviewKeys.lists(), () => loadPromoReviews());

    const { data: news, isSuccess: isNewsSuccess } = useQuery(newsKeys.lists(), () => loadNews());

    useEffect(() => {
        if (isReviewSuccess && reviews.results.length && tnsModule !== null) {
            const carousel = tnsModule.tns({
                container: '#reviewCarousel',
                items: 1,
                controls: false,
                autoHeight: true,
                nav: true,
                navPosition: 'bottom',
                mouseDrag: true,
                autoplay: true,
                autoplayButtonOutput: false
            });
            carousel.events.on('transitionEnd', carousel.updateSliderHeight);
            return () => {
                carousel.destroy(); // we need this because tiny-slider is not reentrant safe
            }
        }
    }, [isReviewSuccess, reviews, tnsModule]);

    useEffect(() => {
        if (isNewsSuccess && tnsModule !== null) {
            const carousel = tnsModule.tns({
                container: '#newsCarousel',
                items: 1,
                controls: false,
                autoHeight: true,
                nav: true,
                navPosition: 'bottom',
                mouseDrag: true
            });
            carousel.events.on('transitionEnd', carousel.updateSliderHeight);
            return () => {
                carousel.destroy(); // we need this because tiny-slider is not reentrant safe
            }
        }
    }, [isNewsSuccess, tnsModule]);

    return (
        <>
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
            { isReviewSuccess && reviews.results.length > 0 && (
                <div className="container py-5 py-sm-6">
                    <div className="row">
                        <div className="col-lg-8 mx-auto">
                            <div id="reviewCarousel">
                                { reviews.results.map((review) => (
                                    <div className="container text-start fs-6">
                                        <ReviewItem review={review} last key={review.id} />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <ParallaxBanner className="vh-100 d-flex align-items-center">
                <ParallaxBannerLayer image="/i/photo/acc.jpg" expanded={false} speed={-20} className="opacity-25" />
                <div className="container py-5 overflow-hidden overlay-content mx-auto text-center">
		            <h1 className="mb-3 display-4 fw-bold text-uppercase">Обзор машин серии Gold Master</h1>
			        <div className="ratio ratio-16x9">
                        <iframe src="https://www.youtube.com/embed/7csbLjVYw68" title="YouTube video player" frameborder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />
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
            { isNewsSuccess && (
                <div className="container py-5 py-sm-6">
                    <div className="row">
                        <div className="col-lg-8 mx-auto">
                            <div id="newsCarousel">
                                { news.map((article) => (
                                    <div className="container text-start" key={article.id}>
                                        <div className="row">
                                            <div className={article.image ? "col-sm-8" : "col"}>
                                                <h3 className="display-6">{ article.title }</h3>
                                                <div className="mb-1 text-muted">{ moment(article.publish_date).format('LL') }</div>
                                                <div className="text-lg" dangerouslySetInnerHTML={{__html: article.content }}></div>
                                            </div>
                                            { article.image && (
                                                <div className="col-sm-4">
                                                    <img className="img-fluid" src={article.image} alt={article.title} />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-4 text-end">
                                <Link className="btn btn-dark" href="/news">Другие новости</Link>
                            </div>
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
        </>
    )
}

Index.getLayout = function getLayout(page) {
    return (
        <ParallaxProvider>
            <Layout transparentHeader>
                {page}
            </Layout>
        </ParallaxProvider>
    )
}

export async function getStaticProps() {
    const queryClient = new QueryClient();
    await queryClient.fetchQuery(newsKeys.lists(), () => loadNews());

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
