import Link from 'next/link';

import rupluralize from '@/lib/rupluralize';
import useBasket from '@/lib/basket';

export default function CartNotice() {
    const { basket, isEmpty } = useBasket();

    if (isEmpty)
        return (
            <div className="my-2"><img src="/i/cart.svg" alt="Корзина" height="33" />Корзина пуста</div>
        );

    return (
        <div className="my-2">
            <Link href="/cart">
                <img src="/i/cart.svg" alt="Корзина" height="33" />
                <span className="fw-bold">{ basket.quantity }</span>
                {' '}{ rupluralize(basket.quantity, ['товар', 'товара', 'товаров']) }
                {' '}на{' '}
                <span className="fw-bold">{ basket.total.toLocaleString('ru') }</span>
                &nbsp;руб
                <span className="btn btn-success btn-sm fw-bold ms-2">Оформить заказ</span>
            </Link>
        </div>
    )
};
