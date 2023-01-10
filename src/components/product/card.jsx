import Link from 'next/link';

import NoImage from '@/components/product/no-image';

import useBasket from '@/lib/basket';

export default function ProductCard({product}) {
    const { addItem } = useBasket();

    const handlePrimaryClick = () => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    return (
        <div className="product_display">
            <div className="thumb text-center">
                <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                    { product.thumbnail ? (
                        <img src={product.thumbnail.url} alt={`${product.title} ${product.whatis}`} />
                    ) : (
                        <NoImage className="text-muted" />
                    )}
                </Link>
            </div>
            <p className="title">
                <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                    { product.title }
                </Link>
            </p>

            <div className="description">
                <p>{ product.whatis } { product.partnumber }</p>
                <div dangerouslySetInnerHTML={{__html: product.shortdescr }} />
            </div>

            { product.price > 0 && (
                <div className="text-center">
                    <div className="mb-2">
                        { product.discount > 0 && (
                            <div className="fs-sm mb-1">
                                <s>{ product.price.toLocaleString('ru') }</s>&nbsp;руб.
                            </div>
                        )}
                        <span className="fw-bold fs-lg">{ product.cost.toLocaleString('ru') }</span>&nbsp;руб.
                    </div>
                    { product.instock > 1 ? (
                        <div className="product-nal-true">Есть в наличии</div>
                    ) : product.instock == 1 ? (
                        <div className="product-nal-true">Мало</div>
                    ) : (
                        <div className="product-nal-false">Закончились</div>
                    )}

                    <button className="btn btn-sm btn-primary fw-bold mt-2" type="button" onClick={handlePrimaryClick}>
                        { product.instock > 0 ? "Купить" : "Сообщить о поступлении" }
                    </button>
                </div>
            )}

            { product.sales_notes && <div className="text-center fs-sm mt-2">{ product.sales_notes }</div> }
        </div>
    )
}
