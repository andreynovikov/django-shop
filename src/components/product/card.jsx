import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import Lightbox from 'yet-another-react-lightbox';

import { IconChevronCompactLeft, IconChevronCompactRight, IconX } from '@tabler/icons-react';

import NoImage from '@/components/product/no-image';
import QuantityInput from '@/components/cart/quantity-input';

import useBasket from '@/lib/basket';
import { productKeys, getProductImages } from '@/lib/queries';

export default function ProductCard({product}) {
    const [item, setItem] = useState(null);
    const [showImage, setShowImage] = useState(false);
    const [currentImageIndex, setCurrentIndex] = useState(0);
    const { basket, addItem, setQuantity, isEmpty, isSuccess, isLoading } = useBasket();

    const router = useRouter();

    const { data: images } = useQuery({
        queryKey: productKeys.images(product.id),
        queryFn: () => getProductImages(product.id),
        enabled: !!product.thumbnail,
        placeholderData: [],
    });

    useEffect(() => {
        if (!isSuccess)
            return;
        let itm = null;
        if (!isEmpty)
            for (var item of basket.items) {
                if (item.product.id === product.id) {
                    itm = item;
                    break;
                }
            }
        setItem(itm);
    }, [basket, isEmpty, isSuccess, product]);

    const handlePrevImage = () => {
        currentImageIndex > 0 && setCurrentIndex(currentImageIndex - 1);
    };

    const handleNextImage = () => {
        currentImageIndex + 1 <= images.length && setCurrentIndex(currentImageIndex + 1);
    };

    const handleClick = () => {
        if (product.variations)
            router.push(product.variations);
        else
            setShowImage(true);
    };

    const updateQuantity = (v) => {
        if (item === null && v > 0)
            addItem(product, v);
        else if (item !== null && v != item.quantity)
            setQuantity(product, v);
    };

    return (
        <div className="sw-p-l card">
            <div className="card-body text-center">
                <a onClick={handleClick} style={{cursor:'pointer'}}>
                    { product.thumbnail ? (
                        <img src={product.thumbnail.url} alt={`${product.title} ${product.whatis}`} />
                    ) : (
                        <NoImage className="text-muted" />
                    )}
                </a>
                <div className="sw-p-l-name">
                    <div className="sw-p-l-action">
                        { product.isnew && <span className="label sw-new">Новинка</span> }
                        { product.recomended && <span className="label sw-recomended">Рекомендуем</span> }
                        { /* TODO - list actions */ }
                    </div>
                    <h3 className="sw-p-l-name-h">
                        { product.variations ? (
                            <Link href={product.variations}>
                                { product.title.replace('Dor Tak','') }
                            </Link>
                        ) : (
                            <a onClick={handleClick} style={{cursor:'pointer'}}>
                                { product.title.replace('Dor Tak','') }
                            </a>
                        )}
                    </h3>
                    { product.whatis && <p>{ product.whatis }</p> }
                    { product.shortdescr && <div className="sw-p-l-brif" dangerouslySetInnerHTML={{__html: product.shortdescr }} /> }
                </div>

                { product.price > 0 && (
                    <div className="mt-2">
                        { product.variations ? (
                            <Link className="btn btn-sm btn-success" role="button" href={product.variations}>
                                Выбрать
                            </Link>
                        ) : (product.ws_pack_only && product.instock >= product.pack_factor) || (!product.ws_pack_only && product.instock > 0) ? (
                            <QuantityInput
                                quantity={item !== null ? item.quantity : undefined}
                                setQuantity={updateQuantity}
                                packOnly={product.ws_pack_only}
                                packFactor={product.pack_factor}
                                isLoading={isLoading} />
                        ) : (
                            <div className="product-nal-false">Закончились</div>
                        )}
                        <div className="mt-2 fs-xs">
                            <span className="fs-base fw-bold">
                                { /* TODO: show user price! */ }
                                { product.cost.toLocaleString('ru') }
                            </span>
                            &#8239;&#8381;
                            { product.ws_pack_only && "/шт." }
                            { (product.ws_pack_only && product.pack_factor !== 1) && (
                                <> Продажа упаковками по { product.pack_factor } шт.</>
                            )}
                        </div>
                    </div>
                )}

                { product.sales_notes && <div className="sw-p-salesnotes text-center">{ product.sales_notes }</div> }
                { product.nal && <p className="text-center">Наличие: <span className="sw-nal">{ product.nal }</span></p> }
                { product.thumbnail && (
                    <Lightbox
                        open={showImage}
                        close={() => setShowImage(false)}
                        slides={[{
                            src: product.big_image ? product.big_image : product.image
                        }, ...images]}
                        carousel={{
                            finite: true
                        }}
                        render={{
                            iconPrev: () => <IconChevronCompactLeft size={64} />,
                            iconNext: () => <IconChevronCompactRight size={64} />,
                            iconClose: () => <IconX size={64} />
                        }}
                    />
                )}
            </div>
        </div>
    );
}
