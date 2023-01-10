import Link from 'next/link';

import rupluralize from '@/lib/rupluralize';
import useBasket from '@/lib/basket';

export default function CartNotice() {
    const { basket, isEmpty } = useBasket();

    if (isEmpty)
        return (
            <span><img src="/i/cart.svg" alt="Корзина" height="33" />Корзина пуста</span>
        );

    return (
        <span>
            <Link href="/cart">
                <img src="/i/cart.svg" alt="Корзина" height="33" />
                <span className="fw-bold text-white">{ basket.quantity }</span>
                {' '}{ rupluralize(basket.quantity, ['товар', 'товара', 'товаров']) }
                {' '}на{' '}
                <span className="fw-bold text-white">{ basket.total.toLocaleString('ru') }</span>
                &nbsp;руб
                <span className="btn btn-warning btn-sm text-white fw-bold ms-2">Оформить заказ</span>
            </Link>
        </span>
    )
};
