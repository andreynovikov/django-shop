import { useState } from 'react';
import Link from 'next/link';

import Collapse from 'react-bootstrap/Collapse';

import CartNotice from '@/components/cart/notice';

export default function Header() {
    const [topMenuOpen, setTopMenuOpen] = useState(false);

    return (
        <header className="container">
            <div className="row">
                <div className="col-sm-4"></div>
                <div className="col-sm-3 d-flex align-items-center justify-content-center">
                    <Link href="/">
                        <img src="/i/logo.svg" alt="DorTak" width="300" className="img-fluid" />
                    </Link>
                </div>
                <div className="col-sm-5 d-flex align-items-center justify-content-center justify-content-md-end">
                    <CartNotice />
                </div>
            </div>
            <nav className="navbar navbar-expand-lg navbar-light bg-light border rounded">
                <div className="container-fluid">
                    <Link className="navbar-brand" href="/">
                        <img alt="DorTak" src="/i/home.svg" width="30" height="30" className="img-fluid" />
                    </Link>
                    <button className="navbar-toggler" type="button" onClick={() => setTopMenuOpen((prevOpen) => !prevOpen)} aria-controls="navbarNav" aria-expanded="false">
                        <span className="navbar-toggler-icon"></span>
                    </button>
                    <Collapse in={topMenuOpen} className="navbar-collapse" id="navbarNav">
                        <div>
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
                        </div>
                    </Collapse>
                </div>
            </nav>
        </header>
    )
}
