import Link from 'next/link'

import CartNotice from '@/components/cart/notice'
import Navbar from '@/components/layout/navbar'
import { buttonClass } from '@/components/ui/button'
import { inputClass } from '@/components/ui/form'
import { navbarClass, navLinkClass, navLinksClass } from '@/components/ui/navbar'

export default function Header() {
  return (
    <header className="container">
      <div className="grid sm:grid-cols-12 sm:gap-x-6">
        <div className="sm:col-span-4"></div>
        <div className="flex items-center justify-center sm:col-span-3">
          <Link href="/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/i/logo.svg" alt="DorTak" width="300" />
          </Link>
        </div>
        <div className="flex items-center justify-center sm:col-span-5 md:justify-end">
          <CartNotice />
        </div>
      </div>
      <nav className={navbarClass}>
        <Navbar
          brand={
            <Link className="me-4 py-[.3125rem]" href="/">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img alt="DorTak" src="/i/home.svg" width="30" height="30" />
            </Link>
          }>
          <ul className={`${navLinksClass} mb-2 lg:me-auto lg:mb-0`}>
            <li>
              <Link className={navLinkClass} href="/catalog/nitki-dor-tak/">Каталоги ниток</Link>
            </li>
            <li>
              <Link className={navLinkClass} href="/pages/price/">Прайс-лист</Link>
            </li>
            <li>
              <Link className={navLinkClass} href="/pages/where-to-buy/">Где купить</Link>
            </li>
            <li>
              <Link className={navLinkClass} href="/user/orders/">Кабинет покупателя</Link>
            </li>
          </ul>
          <form className="flex" action="/search/">
            <input type="search" name="text" className={`${inputClass()} me-2`} placeholder="Введите номер цвета" autoComplete="off" />
            <button type="submit" className={buttonClass({ variant: 'outline-primary' })}>Найти</button>
          </form>
        </Navbar>
      </nav>
    </header>
  )
}
