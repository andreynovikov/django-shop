import { Product } from "@/lib/types"

import { SearchProduct } from "./card"

export default function ProductPrice({ product, delFs, ...props }: { product: Product | SearchProduct, delFs?: string }) {
  if (product.enabled && product.cost > 0)
    return (
      <>
        <span itemProp="price" content={String(product.cost)} {...props}>{product.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
        <meta itemProp="priceCurrency" content="RUB" />
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
