import { dehydrate, QueryClient, useQuery } from 'react-query';
import Link from 'next/link';

import BaseLayout from '@/components/layout/base';
import ProductCard from '@/components/product/card';

import { productKeys, loadProducts } from '@/lib/queries';
import useCatalog from '@/lib/catalog';

const recomendedFilters = [
    { field: 'enabled', value: 1},
    { field: 'recomended', value: 1 },
    { field: 'show_on_sw', value: 1 }
];
const giftsFilters = [
    { field: 'enabled', value: 1},
    { field: 'gift', value: 1 },
    { field: 'show_on_sw', value: 1 }
];
const firstPageFilters = [
    { field: 'enabled', value: 1},
    { field: 'firstpage', value: 1 },
    { field: 'show_on_sw', value: 1 }
];
const sort = '-price';

export default function Index() {
    const { data: recomended, isSuccess: isRecomendedSuccess } = useQuery(
        productKeys.list(null, 24, recomendedFilters, sort),
        () => loadProducts(null, 24, recomendedFilters, sort)
    );
    const { data: gifts, isSuccess: isGiftsSuccess } = useQuery(
        productKeys.list(null, 24, giftsFilters, sort),
        () => loadProducts(null, 24, giftsFilters, sort)
    );
    const { data: firstpage, isSuccess: isFirstPageSuccess } = useQuery(
        productKeys.list(null, 24, firstPageFilters, sort),
        () => loadProducts(null, 24, firstPageFilters, sort)
    );

    useCatalog();

    return (
        <>
            <div class="bg-secondary">
                <section class="pb-5">
                    <div class="bg-dark py-5"></div>
                    <div class="py-3"></div>
                </section>

                <section class="container position-relative pt-3 pt-lg-0 pb-5 mt-n10" style={{zIndex: 10}}>
                    <div class="row">
                        <div class="col-10 offset-1">
                            <div class="card border-0 box-shadow-lg">
                                <div class="card-body px-3 pb-0">
                                    <div class="row g-0 justify-content-center">
                                        <div class="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                                            <Link href="/catalog/sewing_machines/">
                                                <img src="/i/categories/compsewing.svg" alt="Швейные машины" height="75" width="75" />
                                                <div>Швейные машины</div>
                                            </Link>
                                        </div>
                                        <div class="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                                            <Link href="/catalog/embroidery_machines/">
                                                <img src="/i/categories/embroidery.svg" alt="Швейно-вышивальные машины" height="75" width="94" />
                                                <div>Вышивальные машины</div>
                                            </Link>
                                        </div>
                                        <div class="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                                            <Link href="/catalog/sergers/">
                                                <img src="/i/categories/overlock.svg" alt="Оверлоки, коверлоки и распошивальные машины" height="75" width="75" />
                                                <div>Оверлоки и коверлоки</div>
                                            </Link>
                                        </div>
                                        <div class="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                                            <Link href="/catalog/knitting_machines/">
                                                <img src="/i/categories/knitting.svg" alt="Вязальные машины" height="75" width="94" />
                                                <div>Вязальные машины</div>
                                            </Link>
                                        </div>
                                        <div class="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                                            <Link href="/catalog/accessories/">
                                                <img src="/i/categories/accessories.svg" alt="Аксессуары" height="75" width="75" />
                                                <div>Аксессуары</div>
                                            </Link>
                                        </div>
                                        <div class="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                                            <Link href="/catalog/accessories/">
                                                <img src="/i/categories/threads.svg" alt="Аксессуары" height="75" width="75" />
                                                <div>Нитки</div>
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>

            { isRecomendedSuccess && (
                <section className="container pt-5">
                    <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
                        <h2 className="h3 mb-0 pt-3 me-2">Специальные предложения</h2>
                        <div class="pt-3">
                            <Link className="btn btn-outline-accent btn-sm" href="/catalog/promo/">
                                Больше товаров
                                <i class="ci-arrow-right ms-1 me-n1" />
                            </Link>
                        </div>
                    </div>
                    <div className="row pt-2 mx-n2">
                        {recomended.results.map((product) => (
                            <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                                <ProductCard product={product} />
                                <hr className="d-sm-none" />
                            </div>
                        ))}
                    </div>
                </section>
            )}

            { isGiftsSuccess && (
                <section className="container pt-5">
                    <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
                        <h2 className="h3 mb-0 pt-3 me-2">Идеи для подарков</h2>
                    </div>
                    <div className="row pt-2 mx-n2">
                        {gifts.results.map((product) => (
                            <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                                <ProductCard product={product} />
                                <hr className="d-sm-none" />
                            </div>
                        ))}
                    </div>
                </section>
            )}

            { isFirstPageSuccess && (
                <section className="container pt-5">
                    <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
                        <h2 className="h3 mb-0 pt-3 me-2">Новинки</h2>
                        <div class="pt-3">
                            <Link className="btn btn-outline-accent btn-sm" href="/catalog/New/">
                                Больше товаров
                                <i class="ci-arrow-right ms-1 me-n1" />
                            </Link>
                        </div>
                    </div>
                    <div className="row pt-2 mx-n2">
                        {firstpage.results.map((product) => (
                            <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                                <ProductCard product={product} />
                                <hr className="d-sm-none" />
                            </div>
                        ))}
                    </div>
                </section>
            )}

            <div className="bg-faded-primary">
                <section className="container px-0">
                    <div className="row g-0 justify-content-md-center">
                        <div className="col-md-6">
                            <a className="card border-0 rounded-0 text-decoration-none py-md-4 bg-transparent" href="http://www.raruk.ru">
                                <div className="card-body text-center">
                                    <div><i className="ci-edit h3 mt-2 mb-4 text-primary" /></div>
                                    <div className="d-inline-block text-start">
                                        <h2 className="h5 mb-3">Учебный центр &laquo;Радость рукоделия&raquo;</h2>
                                        <p className="text-muted fs-sm mb-1">приглашает на курсы:</p>
                                        <ul className="text-muted fs-sm">
                                            <li>вышивальные программы Pfaff и Husqvarna</li>
                                            <li>технология машинной вышивки на швейно-вышивальных машинах</li>
                                            <li>пэчворк</li>
                                            <li>текстильные сумки</li>
                                            <li>куклы &laquo;Тильда&raquo; и многое другое</li>
                                        </ul>
                                    </div>
                                </div>
                            </a>
                        </div>
                    </div>
                </section>
            </div>
        </>
    )
}

Index.getLayout = function getLayout(page) {
    return (
        <BaseLayout>
            {page}
        </BaseLayout>
    )
}

export async function getStaticProps() {
    const queryClient = new QueryClient();

    await queryClient.prefetchQuery(productKeys.list(null, 24, recomendedFilters, sort), () => loadProducts(null, 24, recomendedFilters, sort));
    await queryClient.prefetchQuery(productKeys.list(null, 24, giftsFilters, sort), () => loadProducts(null, 24, giftsFilters, sort));
    await queryClient.prefetchQuery(productKeys.list(null, 24, firstPageFilters, sort), () => loadProducts(null, 24, firstPageFilters, sort));

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
