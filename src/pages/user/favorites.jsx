import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image'
import { useQuery } from '@tanstack/react-query';

import NoImage from '@/components/product/no-image';
import ProductPrice from '@/components/product/price';
import UserPageLayout from '@/components/layout/user-page';
import UserTopbar from '@/components/user/topbar';

import useBasket from '@/lib/basket';
import useFavorites from '@/lib/favorites';
import { productKeys, loadProducts } from '@/lib/queries';

export default function Favorites() {
    const [filters, setFilters] = useState([]);
    const { addItem } = useBasket();
    const { favorites, unfavoritize } = useFavorites();

    useEffect(() => {
        setFilters(favorites.reduce((filters, id) => {
            filters.push({field: 'id', value: id});
            return filters;
        }, []));
    }, [favorites]);

    const { data: products, isSuccess } = useQuery({
        queryKey: productKeys.list(1, 999, filters, 'title'),
        queryFn: () => loadProducts(1, 999, filters, 'title'),
        enabled : filters.length > 0
    });

    const handleClick = (product) => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    return (
        <>
            <UserTopbar>
                <div className="d-flex w-100 text-light text-center me-3"></div>
            </UserTopbar>
            { favorites.length > 0 ? (
                isSuccess && products.results.map((product, index) => (
                    <div className={"d-sm-flex justify-content-between mt-lg-4 mb-4 pb-3 pb-sm-2" + (index < favorites.length - 1 ? " border-bottom" : "")} key={product.id}>
                        <div className="d-block d-sm-flex align-items-start text-center text-sm-start">
                            <Link className="d-block flex-shrink-0 mx-auto me-sm-4" style={{width: "10rem"}} href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                                { product.image ? (
                                    <div className="position-relative" style={{ width: 160, height: 160 }}>
                                        <Image
                                            src={product.image}
                                            fill
                                            style={{ objectFit: 'contain' }}
                                            alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
                                    </div>
                                ) : (
                                    <NoImage size={160} />
                                )}
                            </Link>
                            <div className="pt-2">
                                <h3 className="product-title fs-base mb-2">
                                    <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                                        { product.title }
                                    </Link>
                                </h3>
                                { (product.whatis || product.partnumber) && <div className="product-meta fs-sm">{ product.whatis } { product.partnumber }</div> }
                                { product.sales_notes && <div className="fs-ms text-info">{ product.sales_notes }</div> }
                                <div className="fs-lg text-accent pt-2"><ProductPrice product={product} /></div>
                            </div>
                        </div>
                        <div className="pt-2 ps-sm-3 mx-auto mx-sm-0 text-center text-nowrap">
                            { product.enabled && product.instock > 0 && (
                                <button className="btn btn-success btn-sm me-2" type="button" onClick={() => handleClick(product)}>
                                    <i className="ci-cart fs-sm me-1" />
                                    { product.variations ? "Выбрать" : "Купить" }
                                </button>
                            )}
                            <button className="btn btn-outline-danger btn-sm" type="button" onClick={() => unfavoritize(product.id)}>
                                <i className="ci-trash me-2" />Удалить
                            </button>
                        </div>
                    </div>
                ))
            ) : (
                <p className="lead">Здесь появятся отложенные ваши товары</p>
            )}
        </>
    )
}

Favorites.getLayout = function getLayout(page) {
    const breadcrumbs = [
        {
            label: 'Личный кабинет',
            href: '/user/profile'
        }
    ]
    return (
        <UserPageLayout title="Избранное" breadcrumbs={breadcrumbs}>
            {page}
        </UserPageLayout>
    )
}
