import Link from 'next/link';

import NoImage from '@/components/product/no-image';

import useBasket from '@/lib/basket';

export default function ProductCard({product}) {
    const { addItem } = useBasket();

    const handlePrimaryClick = () => {
        if (product.variations) {
        } else {
            addItem(product);
        }
    };

    return (
        <div className="sw-p-l card">
            <div className="card-body">
                <div className="text-center">
                    <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                        { product.thumbnail ? (
                            <img src={product.thumbnail.url} alt={`${product.title} ${product.whatis}`} />
                        ) : (
                            <NoImage size={120} stroke={1.5} className="text-muted" />
                        )}
                    </Link>
                </div>
                <div className="sw-p-l-name">
                    <div className="sw-p-l-action">
                        { product.ishot && <span className="label sw-action">Акция</span> }
                        { product.isnew && <span className="label sw-new">Новинка</span> }
                        { product.recomended && <span className="label sw-recomended">Рекомендуем</span> }
                        { product.utilisation && <span className="label sw-action">Скидка по &laquo;Утилизации&raquo;</span> }
                    </div>
                    <h3 className="sw-p-l-name-h">
                        <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                            { product.title }
                        </Link>
                    </h3>
                    <p>{ product.whatis } { product.partnumber }</p>

                    <div className="sw-p-l-brif" dangerouslySetInnerHTML={{__html: product.shortdescr }} />
                </div>

                { product.price > 0 && (
                    <div className="text-center">
                        <div className="mb-2">
                            { product.discount > 0 && (
                                <><s className="sw-p-l-oldprice">{ product.price.toLocaleString('ru') }</s>&nbsp;руб.</>
                            )}
                            <span className="sw-p-l-price">{ product.cost.toLocaleString('ru') }</span>&nbsp;руб.
                        </div>
                        { product.instock > 1 ? (
                            <div className="product-nal-true">Есть в наличии</div>
                        ) : product.instock == 1 ? (
                            <div className="product-nal-true">Мало</div>
                        ) : (
                            <div className="product-nal-false">Закончились</div>
                        )}
                        <button className="btn btn-sm btn-success fs-xs fw-bold mt-2" type="button" onClick={handlePrimaryClick}>
                            { product.instock > 0 ? "Купить" : "Сообщить о поступлении" }
                        </button>
                    </div>
                )}

                { product.wb_link && <div className="text-center mt-2">
                    <a href={product.wb_link} className="btn btn-sm sw-btn-wb fs-xs fw-bold" role="button">Купить на WB</a>
                </div> }
                { product.ozon_link && <div className="text-center mt-2">
                    <a href={ product.ozon_link } className="btn btn-sm sw-btn-ozon fs-xs fw-bold" role="button">Купить на Ozon</a>
                </div> }

                { product.sales_notes && <div className="sw-p-salesnotes text-center">{ product.sales_notes }</div> }
                { product.nal && <p className="text-center">Наличие: <span className="sw-nal">{ product.nal }</span></p> }
            </div>
        </div>
    )
}
