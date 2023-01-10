import Link from 'next/link';

import Layout from '@/components/layout';

export default function Index() {
    return (
        <div className="d-flex flex-wrap justify-content-between py-2" style={{gap: "20px"}}>
            <div className="product_display text-center">
                <h3>
                    <Link href="/catalog/electronic/">Электронные машины</Link>
                </h3>
                <div className="thumb">
                    <Link href="/catalog/electronic/">
                        <img src="/media/images/Singer/Singer9960.jpg" alt="Электронные машины" />
                    </Link>
                </div>
            </div>
            <div className="product_display text-center">
                <h3>
                    <Link href="/catalog/basic/">Механические машины</Link>
                </h3>
                <div className="thumb">
                    <Link href="/catalog/basic/">
                        <img src="/media/images/Singer/Singer_2290.jpg" alt="Механические машины" />
                    </Link>
                </div>
            </div>
            <div className="product_display text-center">
                <h3>
                    <Link href="/catalog/serger/">Оверлоки</Link>
                </h3>
                <div className="thumb">
                    <Link href="/catalog/serger/">
                        <img src="/media/images/Singer/Singer_14hd854.jpg" alt="Оверлоки" />
                    </Link>
                </div>
            </div>
            <div className="product_display text-center">
                <h3>
                    <Link href="/catalog/irons/">Уход за домом</Link>
                </h3>
                <div className="thumb">
                    <Link href="/catalog/irons/">
                        <img src="/media/images/Singer/Singer4020.jpg" alt="Уход за домом" />
                    </Link>
                </div>
            </div>
            <div className="product_display text-center">
                <h3>
                    <Link href="/catalog/Feet/">Лапки</Link>
                </h3>
                <div className="thumb">
                    <Link href="/catalog/Feet/">
                        <img src="/media/categories/featured-presser_feet_pzJu4kE.png" alt="Лапки" />
                    </Link>
                </div>
            </div>
            <div className="product_display text-center">
                <h3>
                    <Link href="/catalog/Accessories/">Аксессуары</Link>
                </h3>
                <div className="thumb">
                    <Link href="/catalog/Accessories/">
                        <img src="/media/categories/featured-notions_rmKezuP.png" alt="Аксессуары" />
                    </Link>
                </div>
            </div>
        </div>
    )
}

Index.getLayout = function getLayout(page) {
    return (
        <Layout hideTitle>
            {page}
        </Layout>
    )
}
