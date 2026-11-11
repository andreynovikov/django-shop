'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useQuery } from '@tanstack/react-query'

import { IconShoppingCart, IconTrash } from '@tabler/icons-react'

import { ButtonLoading } from '@/components/loading'
import NoImage from '@/components/product/no-image'
import { buttonClass } from '@/components/ui/button'
import ProductPrice from '@/components/product/price'
import UserTopbar from '@/components/user/topbar'

import useBasket from '@/lib/basket'
import useFavorites from '@/lib/favorites'
import { productKeys, loadProducts } from '@/lib/queries'
import { ProductInfo } from '@/lib/types'

export default function UserFavorites() {
  const { addItem, addingProductId } = useBasket()
  const { favorites, unfavoritize } = useFavorites()

  const { data: products, isSuccess } = useQuery({
    queryKey: productKeys.list(1, 999, { id: favorites }, 'title'),
    queryFn: () => loadProducts(1, 999, { id: favorites }, 'title'),
    enabled: favorites.length > 0
  })

  const handleClick = (product: ProductInfo) => {
    if (!product.variations)
      addItem(product)
  }

  return (
    <>
      <UserTopbar>
        <div className="me-4 flex w-full text-center text-white">&nbsp;</div>
      </UserTopbar>
      {favorites.length > 0 ? (
        isSuccess && products.results.map((product, index) => (
          <div className={`mb-6 pb-4 sm:flex sm:justify-between sm:pb-2 lg:mt-6 ${index < favorites.length - 1 ? "border-b" : ""}`} key={product.id}>
            <div className="block text-center sm:flex sm:items-start sm:text-start">
              <Link className="mx-auto block w-40 shrink-0 sm:me-6" href={`/products/${product.code}`}>
                {product.image ? (
                  <div className="relative size-40">
                    <Image
                      src={product.image}
                      fill
                      style={{ objectFit: 'contain' }}
                      sizes="160px"
                      alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
                  </div>
                ) : (
                  <NoImage size={160} />
                )}
              </Link>
              <div className="pt-2">
                <h3 className="mb-2 text-base leading-[1.2] font-medium">
                  <Link className="text-heading hover:text-primary" href={`/products/${product.code}`}>
                    {product.title}
                  </Link>
                </h3>
                {(product.whatis || product.partnumber) && <div className="text-sm text-muted">{product.whatis} {product.partnumber}</div>}
                {product.sales_notes && <div className="text-ms text-info">{product.sales_notes}</div>}
                <div className="pt-2 text-lg text-accent"><ProductPrice product={product} /></div>
              </div>
            </div>
            <div className="mx-auto pt-2 text-center whitespace-nowrap sm:mx-0 sm:ps-4">
              {product.enabled && product.instock > 0 && (
                <button className={`${buttonClass({ variant: 'success', size: 'sm' })} me-2`} type="button" onClick={() => handleClick(product)} disabled={addingProductId === product.id}>
                  <IconShoppingCart size={14} stroke={1.5} className="me-1" />
                  {product.variations ? "Выбрать" : "Купить"}
                  {addingProductId === product.id && <ButtonLoading />}
                </button>
              )}
              <button className={buttonClass({ variant: 'outline-danger', size: 'sm' })} type="button" onClick={() => unfavoritize(product.id)}>
                <IconTrash size={14} stroke={1.5} className="me-2" />Удалить
              </button>
            </div>
          </div>
        ))
      ) : (
        <p className="mb-4 text-xl font-light">Здесь появятся ваши отложенные товары</p>
      )}
    </>
  )
}
