import Link from 'next/link';

import CartNotice from '@/components/cart/notice';
import ProductSearchInput from '@/components/product/search-input';

export default function Header() {
    return (
        <div className="row top-content">
            <div className="col-md-6 sw-logo">
                <Link href="/">
                    <img src="/i/janomelogo.svg" alt="Швейные машины Janome" className="img-responsive" />
                </Link>
            </div>
            <div className="col-md-6 text-end fs-sm">
                <div className="ja-title">
                    <strong>
                        Фирменный интернет-магазин швейных машин <span>Janome</span>
                        <br />+7 495 766-56-75
                    </strong>
                </div>
                <ProductSearchInput />
                <CartNotice />
            </div>
        </div>
    )
}
