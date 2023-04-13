import Link from 'next/link';

import rupluralize from '@/lib/rupluralize';
import useBasket from '@/lib/basket';

export default function CartNotice() {
    const { basket, isEmpty } = useBasket();

    if (isEmpty)
        return (
            <span className="text-center text-sm-end my-1">
                <img src="/i/cart.svg" alt="Корзина" height="33" />Корзина пуста
            </span>
        );

    return (
        <span className="text-center text-sm-end my-2">
            <Link href="/cart">
                <img src="/i/cart.svg" alt="Корзина" height="33" />
                {' '}
                <span className="text-nowrap">
                    <span className="fw-bold">{ basket.quantity }</span>
                    {' '}{ rupluralize(basket.quantity, ['товар', 'товара', 'товаров']) }
                    {' '}на{' '}
                    <span className="fw-bold">{ basket.total.toLocaleString('ru') }</span>
                    &nbsp;руб
                </span>
                <span className="btn btn-success btn-sm text-white fw-bold ms-2">Оформить заказ</span>
            </Link>
        </span>
    )
};
