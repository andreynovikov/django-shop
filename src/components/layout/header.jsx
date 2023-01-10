import { forwardRef } from 'react';
import Link from 'next/link';

import Dropdown from 'react-bootstrap/Dropdown';

import CartNotice from '@/components/cart/notice';
import ProductSearchInput from '@/components/product/search-input';

export default function Header() {
    const MegaMenu = forwardRef(({ style, className, 'aria-labelledby': labeledBy }, ref) => (
        <div
            ref={ref}
            style={style}
            className={className + " si-mega-menu rounded-0 shadow border-0 mt-2"}
            aria-labelledby={labeledBy}>
            <div className="container-fluid p-3">
                <div className="row">
                    <div className="col-md-3 fw-bold text-center mb-3">
                        <Dropdown.Item as={Link} href="/catalog/electronic/">
                            <img src="/i/newsingerco/productsElectronic.jpg" alt="Электронные швейные машины" width="147" height="102" />
                            <div>Электронные машины</div>
                        </Dropdown.Item>
                    </div>
                    <div className="col-md-3 fw-bold text-center mb-3">
                        <Dropdown.Item as={Link} href="/catalog/basic/">
                            <img src="/i/newsingerco/productsMechanical.jpg" alt="Механические швейные машины" width="147" height="102" />
                            <div>Механические машины</div>
                        </Dropdown.Item>
                    </div>
                    <div className="col-md-3 fw-bold text-center mb-3">
                        <Dropdown.Item as={Link} href="/catalog/serger/">
                            <img src="/i/newsingerco/productsSerger.jpg" alt="Оверлоки" width="147" height="102" />
                            <div>Оверлоки</div>
                        </Dropdown.Item>
                    </div>
                    <div className="col-md-3 fw-bold text-center mb-3">
                        <Dropdown.Item as={Link} href="/catalog/irons/">
                            <img src="/i/newsingerco/productsGarment.jpg" alt="Уход за одеждой и домом" width="147" height="102" />
                            <div>Уход за одеждой и домом</div>
                        </Dropdown.Item>
                    </div>
                </div>
                <div className="row">
                    <div className="col-md-3 fw-bold text-center mb-3">
                        <Dropdown.Item as={Link} href="/catalog/Feet/">
                            <img src="/i/newsingerco/productsFeet.jpg" alt="Лапки для швейных машин" width="147" height="102" />
                            <div>Лапки</div>
                        </Dropdown.Item>
                    </div>
                    <div className="col-md-3 fw-bold text-center mb-3">
                        <Dropdown.Item as={Link} href="/catalog/Accessories/">
                            <img src="/i/newsingerco/productsNotions.jpg" alt="Аксессуары" width="147" height="102" />
                            <div>Аксессуары</div>
                        </Dropdown.Item>
                    </div>
                </div>
            </div>
        </div>
    ));
    MegaMenu.displayName = 'MegaMenu';

    return (
        <header>
            <div className="row">
                <div className="col-sm-6 p-2">
                    <Link href="/">
                        <img src="/i/newsingerco/logo_singer.png" alt="Singer logo" width="323" height="105" />
                    </Link>
                </div>
                <div className="col-sm-6 p-3 text-center text-sm-end" id="secondaryNavigation">
                    <Link className="d-block mb-1 d-sm-inline mb-sm-0" href="/user/orders">Мои заказы</Link>
                    <span className="d-none d-sm-inline">&nbsp;&nbsp;|&nbsp;&nbsp;</span>
                    <CartNotice />
                    <ProductSearchInput />
                </div>
            </div>
            <div id="navigation">
                <Dropdown as="div">
                    <Dropdown.Toggle as="a" className="navLink">ПРОДУКЦИЯ</Dropdown.Toggle>
                    <Dropdown.Menu as={MegaMenu} />
                </Dropdown>
                <div>
                    <Link className="navLink" href="/pages/delivery">ДОСТАВКА И ОПЛАТА</Link>
                </div>
                <div>
                    <Link className="navLink" href="/pages/where-to-buy">ГДЕ КУПИТЬ</Link>
                </div>
            </div>
        </header>
    )
}
