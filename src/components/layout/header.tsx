import Link from 'next/link'

import CartNotice from '@/components/cart/notice'
import ProductSearchInput from '@/components/product/search-input'
import ProductsMenu from '@/components/layout/products-menu'

export default function Header() {
  return (
    <header>
      <div className="-mx-3 flex flex-wrap">
        <div className="w-full p-2 sm:w-1/2">
          <Link href="/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/i/newsingerco/logo_singer.png" alt="Singer logo" width="323" height="105" />
          </Link>
        </div>
        <div className="w-full p-4 text-center sm:w-1/2 sm:text-end" id="secondaryNavigation">
          <Link className="mb-1 block sm:mb-0 sm:inline" href="/user/orders/">Мои заказы</Link>
          <span className="hidden sm:inline">&nbsp;&nbsp;|&nbsp;&nbsp;</span>
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
