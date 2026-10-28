import { Product, ProductInfo } from "@/lib/types"

import { SearchProduct } from "./card"

interface ProductPriceProps {
  product: Product | ProductInfo | SearchProduct
  delFs?: string
  microdata?: boolean  // price properties of the enclosing schema.org Offer
}

export default function ProductPrice({ product, delFs, microdata = false, ...props }: ProductPriceProps) {
  if (product.enabled && product.cost > 0)
    return (
      <>
        {microdata ? (
          <>
            <span itemProp="price" content={String(product.cost)} {...props}>{product.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
            <meta itemProp="priceCurrency" content="RUB" />
          </>
        ) : (
          <span {...props}>{product.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
        )}
        {product.cost != product.price && (
          <>
            {" "}
            <del className={`fs-${delFs ? delFs : "sm"} text-muted`}>
              {product.price.toLocaleString('ru')}
              <small>&nbsp;руб</small>
            </del>
          </>
        )}
      </>
    )
  else
    return <small>товар снят с продажи</small>
}
