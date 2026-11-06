import Link from 'next/link'

import CartNotice from '@/components/cart/notice'
import Navbar from '@/components/layout/navbar'

export default function Header() {
  return (
    <header className="container">
      <div className="row">
        <div className="col-sm-4"></div>
        <div className="col-sm-3 d-flex align-items-center justify-content-center">
          <Link href="/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/i/logo.svg" alt="DorTak" width="300" className="img-fluid" />
          </Link>
        </div>
        <div className="col-sm-5 d-flex align-items-center justify-content-center justify-content-md-end">
          <CartNotice />
        </div>
      </div>
      <nav className="navbar navbar-expand-lg navbar-light bg-light border rounded">
        <Navbar
          brand={
            <Link className="navbar-brand" href="/">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img alt="DorTak" src="/i/home.svg" width="30" height="30" className="img-fluid" />
            </Link>
          }>
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <Link className="nav-link" href="/catalog/nitki-dor-tak/">Каталоги ниток</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" href="/pages/price/">Прайс-лист</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" href="/pages/where-to-buy/">Где купить</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" href="/user/orders/">Кабинет покупателя</Link>
            </li>
          </ul>
          <form className="d-flex" action="/search/">
            <input type="search" name="text" className="form-control me-2" placeholder="Введите номер цвета" autoComplete="off" />
            <button type="submit" className="btn btn-outline-primary">Найти</button>
          </form>
        </Navbar>
      </nav>
    </header>
  )
}
