import { useState, useMemo } from 'react'

import useBasket from '@/lib/basket'

export default function ProductShopping({ product }) {
  const [quantity, setAddQuantity] = useState(1)
  const { basket, addItem, removeItem, setQuantity, isEmpty, isSuccess } = useBasket()

  const basketQuantity = useMemo(() => {
    if (!isSuccess || isEmpty)
      return 0
    const items = basket.items.filter(item => item.product.id == product.id)
    if (items.length > 0)
      return items[0].quantity
    else
      return 0
  }, [basket, product, isSuccess, isEmpty])

  const handleSetQuantity = (delta) => {
    const quantity = Math.max(0, Math.min(10000, basketQuantity + delta))
    if (quantity === 0)
      removeItem(product.id)
    else
      setQuantity(product.id, quantity)
  }

  const handleCartClick = () => {
    // TODO: {% if utm_source %}?utm_source={{ utm_source }}{% endif %}
    addItem(product.id, quantity)
  }

  return basketQuantity > 0 ? (
    <>
      <button className="btn btn-success btn-shadow d-block px-5" type="button" onClick={() => handleSetQuantity(-1)}>
        <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        -
      </button>
      <span className="px-2">
        В корзине: {basketQuantity} шт
      </span>
      <button className="btn btn-success btn-shadow d-block px-5" type="button" onClick={() => handleSetQuantity(+1)}>
        <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        +
      </button>
    </>
  ) : (
    <>
      {product.instock > 5 && (
        <select className="form-select me-3" style={{ width: "5rem" }} value={quantity} onChange={(e) => setAddQuantity(e.target.value)}>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5</option>
        </select>
      )}
      <button className="btn btn-success btn-shadow d-block w-100" type="button" onClick={handleCartClick}>
        <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        <i className="ci-cart fs-lg me-2" />Купить
      </button>
    </>
  )
}