/* eslint-disable @next/next/no-img-element */
import Link from 'next/link';

export default function TopCategoriesCard() {
    return (
        <div className="card border-0 box-shadow-lg">
            <div className="card-body px-3 pb-0">
                <div className="row g-0 justify-content-center">
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/promo/">
                            <img src="/i/categories/sale.svg" alt="Специальные предложения" height="75" width="75" />
                            <div>Специальные предложения</div>
                        </Link>
                    </div>
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/sewing_machines/">
                            <img src="/i/categories/compsewing.svg" alt="Швейные машины" height="75" width="75" />
                            <div>Швейные машины</div>
                        </Link>
                    </div>
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/embroidery_machines/">
                            <img src="/i/categories/embroidery.svg" alt="Швейно-вышивальные машины" height="75" width="94" />
                            <div>Вышивальные машины</div>
                        </Link>
                    </div>
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/sergers/">
                            <img src="/i/categories/overlock.svg" alt="Оверлоки, коверлоки и распошивальные машины" height="75" width="75" />
                            <div>Оверлоки и коверлоки</div>
                        </Link>
                    </div>
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/knitting_machines/">
                            <img src="/i/categories/knitting.svg" alt="Вязальные машины" height="75" width="94" />
                            <div>Вязальные машины</div>
                        </Link>
                    </div>
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/accessories/">
                            <img src="/i/categories/accessories.svg" alt="Аксессуары" height="75" width="75" />
                            <div>Аксессуары</div>
                        </Link>
                    </div>
                    { /*
                    <div className="col-6 col-md-4 col-lg-2 mb-grid-gutter text-center">
                        <Link href="/catalog/accessories/threads/">
                            <img src="/i/categories/threads.svg" alt="Нитки" height="75" width="75" />
                            <div>Нитки</div>
                        </Link>
                    </div>
                      */
                    }
                </div>
            </div>
        </div>
    )
}
