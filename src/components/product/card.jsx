import Link from 'next/link';
import Image from 'next/image';

import { IconSearch } from '@tabler/icons-react';

import SvgIcon from '@/components/svg-icon';

const noImageStyle = {
    width: '350px',
    height: '350px',
    fontSize: '150px',
    padding: '100px'
}

export default function ProductCard({product}) {
    return (
        <div className="product">
            <div className="product-image text-center">
                { product.ishot && <div className="ribbon ribbon-dark">Акция</div> }
                { product.isnew && <div className="ribbon ribbon-primary">Новинка</div> }
                { product.recomended && <div className="ribbon ribbon-info">Рекомендуем</div> }
                { product.image ? (
                  <div className="position-relative" style={{ width: 350, aspectRatio: 1 }}>
                      <Image
                          src={product.image}
                          fill
                          style={{ objectFit: "contain" }}
                          sizes="350px"
                          loading="lazy"
                          alt={`${product.title} ${product.whatisit ?? product.whatis}`} />
                    </div>
                ) : (
                    <SvgIcon id="shipping-box-1" className="svg-icon d-inline-block text-muted" style={ noImageStyle } />
                )}
                <div className="product-hover-overlay">
                    <Link className="product-hover-overlay-link" href={{ pathname: '/products/[code]', query: { code: product.code }}} />
                    <div className="product-hover-overlay-buttons">
                        { /*
                        <a class="btn btn-outline-dark btn-product-left d-none d-sm-inline-block" href="#">
                            <i class="fa fa-shopping-cart"></i>
                        </a>
                          */
                        }
                        <Link className="btn btn-dark btn-buy" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                            <IconSearch />
                            <span className="btn-buy-label ms-2">Подробнее</span>
                        </Link>
                        { /*
                        <a class="btn btn-outline-dark btn-product-right d-none d-sm-inline-block" href="#">
                            <i class="fa fa-expand-arrows-alt"></i>
                        </a>
                          */
                        }
                    </div>
                </div>
            </div>
            <div className="py-2">
                <p className="text-muted text-sm mb-1">{ product.whatis }</p>
                <h3 className="h6 text-uppercase mb-1">
                    <Link className="text-dark" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                        { product.title }
                    </Link>
                </h3>
            </div>
        </div>
    )
}
