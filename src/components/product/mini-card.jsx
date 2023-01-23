import Link from 'next/link';

import ProductPrice from '@/components/product/price';

const noImageStyle = {
    width: '200px',
    height: '200px',
    fontSize: '100px',
    padding: '50px'
}

export default function ProductMiniCard({product}) {
    return (
        <div className="card product-card card-static">
            <Link className="d-inline-block mx-auto overflow-hidden" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                { product.thumbnail ? (
                    <img
                        src={product.thumbnail.url}
                        width={product.thumbnail.width}
                        height={product.thumbnail.height}
                        alt={`${product.title} ${product.whatis}`} />
                ) : (
                    <i className="d-inline-block ci-camera text-muted" style={ noImageStyle } />
                )}
            </Link>
            <div className="card-body py-2">
                <Link className="product-meta d-block fs-xs pb-1" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                    { product.whatis } { product.partnumber }
                </Link>
                <h3 className="product-title fs-sm">
                    <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                        { product.title }
                    </Link>
                </h3>
                <div className="d-flex justify-content-between">
                    <div className="product-price text-accent"><ProductPrice product={product} /></div>
                </div>
            </div>
        </div>
    )
}
