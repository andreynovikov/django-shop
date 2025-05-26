import Link from 'next/link';

export default function Footer() {
    return (
        <>
            <div className="row bottom-content mt-5">
                <div className="col-md-4">
                    <Link href="/pages/map/">
                        <img src="/i/mc15k-nav-icon-features.png" alt="Наш адрес" width="145" height="100" />
                        <h5 className="bottom">Наш адрес</h5>
                        <p className="bottom">Наш магазин находится в Москве, рядом с метро &laquo;Пролетарская&raquo;</p>
                    </Link>
                </div>
                <div className="col-md-4">
                    <Link href="/pages/delivery/">
                        <img src="/i/mc15k-nav-icon-delivery.png" alt="Доставка" width="145" height="100" />
                        <h5 className="bottom">Доставка</h5>
                        <p className="bottom">Условия доставки и оплаты товаров</p>
                    </Link>
                </div>
                <div className="col-md-4">
                    <Link href="/user/orders/">
                        <img src="/i/cart.png" alt="Доставка" width="145" height="100" />
                        <h5 className="bottom">Кабинет покупателя</h5>
                        <p className="bottom">Узнать состояние заказа</p>
                    </Link>
                </div>
            </div>
            <div className="row footer p-4">
                <div className="col-md-6">
                    <p>
                        Copyright (C) 2013-2025{' '}
                        <a href="http://www.janome.co.jp/e1.htm">Janome</a>
                        {' '}&amp;{' '}
                        <a href="http://www.sewing-world.ru">Швейный Мир</a>
                    </p>
                </div>
                <div className="col-md-6">
                    <p>info@janome.club</p>
                </div>
            </div>
        </>
    )
}
