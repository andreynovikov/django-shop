import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useMutation, useQueryClient } from 'react-query';

import Layout from '@/components/layout';
import LoginForm from '@/components/user/login-form';
import CartItem from '@/components/cart/item';

import useBasket from '@/lib/basket';
import { useSession, signOut, invalidate } from '@/lib/session';
import { orderKeys, createOrder } from '@/lib/queries';

export default function Cart() {
    const { user, registered, status } = useSession();
    const { basket, isEmpty, isLoading, isSuccess, removeItem, setQuantity } = useBasket();

    const router = useRouter();
    const queryClient = useQueryClient();

    const createOrderMutation = useMutation(() => createOrder(), {
        onSuccess: (data) => {
            queryClient.invalidateQueries(orderKeys.lists());
            queryClient.setQueryData(orderKeys.detail(data.id), data);
            sessionStorage.setItem('lastOrder', data.id);
            router.push('/confirmation');
            console.log(data);
        },
        onError: (error) => {
            console.error(error);
        }
    });

    useEffect(() => {
        console.log("order", registered, status);
        if (status === 'authenticated' && registered) {
            createOrderMutation.mutate();
            invalidate();
        }
    }, [registered, status]);

    const handleCreateOrder = () => {
        createOrderMutation.mutate();
    };

    if (!isSuccess || isEmpty)
        return (
            <section className="col-lg-8">
                { isLoading ? (
                        <div className="spinner-border" style={{width: "5rem", height: "5rem"}} role="status">
                        <span className="visually-hidden">Загружается...</span>
                    </div>
                ) : isEmpty ? (
                    <div className="d-flex flex-row align-items-center">
                        <div className="lead">Положите в корзину товар для оформления заказа</div>
                    </div>
                ) : (
                    <div className="lead">Что-то пошло не так...</div>
                )}
            </section>
        );

    return (
        <>
            <section className="col-lg-8">
                {basket.items.map((item, index) => (
                    <CartItem key={item.product.id} item={item} first={index === 0} last={index === basket.items.length - 1} removeItem={removeItem} setQuantity={setQuantity} />
                ))}
            </section>
            <aside className="col-lg-4 pt-4 pt-lg-0 ps-xl-5">
                <div className="bg-white rounded-3 shadow-lg p-4">
                    <div className="py-2 px-xl-2">
                        <div className="text-center mb-4 pb-3 border-bottom">
                            <h2 className="h5 mb-3 pb-1">Итого</h2>
                            <h3 className="fw-normal mb-0">{ basket.total.toLocaleString('ru') }<small>&nbsp;руб</small></h3>
                            <div className="fs-sm text-muted">без учета стоимости доставки</div>
                        </div>

                        { status === 'authenticated' ? (
                            <>
                                <div className="mb-2">Добро пожаловать, { user?.name || "уважаемый покупатель" }!</div>
                                <button className="btn btn-primary btn-shadow d-block w-100 mt-4" type="button" onClick={handleCreateOrder}>
                                    Оформить заказ
                                </button>
                            </>
                        ) : (
                            <LoginForm embedded={true} ctx="order" />
                        )}

                        <div id="oferta-notice" className="mt-4 fs-xs">
                            Нажимая на кнопку &laquo;Оформить заказ&raquo;, вы подтверждаете согласие с условиями{' '}
                            <Link href="/pages/oferta/">публичной оферты</Link>.
                        </div>

                        { status === 'authenticated' && (
                            <div className="mt-3">
                                <a className="fs-sm link-primary" onClick={signOut} style={{cursor:'pointer'}}>Оформить заказ от другого имени</a>
                            </div>
                        )}
                    </div>
                </div>
            </aside>
        </>
    )
}

Cart.getLayout = function getLayout(page) {
    return (
        <Layout title="Корзина" hideTitleBorder>
            <div className="row">
                {page}
            </div>
        </Layout>
    )
}
