export default function ProductPrice({ product, delFs, ...props }) {
  if (product.enabled && product.cost > 0)
    return (
      <>
        <span itemProp="price" content={product.cost} {...props}>{product.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
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
