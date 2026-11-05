import Link from 'next/link'

import CartNotice from '@/components/cart/notice'
import ProductSearchInput from '@/components/product/search-input'
import ProductsMenu from '@/components/layout/products-menu'

export default function Header() {
  return (
    <header>
      <div className="row">
        <div className="col-sm-6 p-2">
          <Link href="/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/i/newsingerco/logo_singer.png" alt="Singer logo" width="323" height="105" />
          </Link>
        </div>
        <div className="col-sm-6 p-3 text-center text-sm-end" id="secondaryNavigation">
          <Link className="d-block mb-1 d-sm-inline mb-sm-0" href="/user/orders/">Мои заказы</Link>
          <span className="d-none d-sm-inline">&nbsp;&nbsp;|&nbsp;&nbsp;</span>
          <CartNotice />
          <ProductSearchInput />
        </div>
      </div>
      <div id="navigation">
        <ProductsMenu />
        <div>
          <Link className="navLink" href="/pages/delivery/">ДОСТАВКА И ОПЛАТА</Link>
        </div>
        <div>
          <Link className="navLink" href="/pages/where-to-buy/">ГДЕ КУПИТЬ</Link>
        </div>
      </div>
    </header>
  )
}
