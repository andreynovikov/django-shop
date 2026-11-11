'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useQuery, useQueries } from '@tanstack/react-query'
import { useQueryStates, parseAsInteger, parseAsNativeArrayOf } from 'nuqs'

import FieldHelp from '@/components/product/field-help'
import { IconTrash } from '@tabler/icons-react'

import { Alert } from '@/components/ui/alert'
import { buttonClass } from '@/components/ui/button'
import { checkClass, checkInputClass, checkLabelClass } from '@/components/ui/form'
import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'
import { ButtonLoading, PageLoading } from '@/components/loading'

import useBasket from '@/lib/basket'
import useComparison from '@/lib/comparison'
import { deepCompare } from '@/lib/compare'
import { prettifyProductFieldValue } from '@/lib/format'
import { kindKeys, productKeys, loadKinds, loadKind, loadProduct, getProductFields } from '@/lib/queries'
import { Product } from '@/lib/types'

// ?kind= picks the compared products of a kind, ?product=&product= are the products to show
const comparisonParams = {
  kind: parseAsInteger,
  product: parseAsNativeArrayOf(parseAsInteger),
}

// Reading the query needs a Suspense boundary, the page is static
// A bordered table cell and the field name at the start of a row
const cellClass = 'border p-3'
const headerCellClass = 'border p-3 text-start font-medium text-heading first-letter:uppercase'

export default function ProductComparison() {
  const [{ kind: kindId, product: productIds }, setParams] = useQueryStates(comparisonParams)
  const { addItem, addingProductId } = useBasket()

  const [different, setDifferent] = useState(false)

  // if kind is passed get filtered product list...
  const { comparisons, uncompare, isSuccess: isComparisonSuccess } = useComparison({ kind: kindId })

  // ...and redirect to explicit comparison
  useEffect(() => {
    if (kindId !== null && isComparisonSuccess)
      setParams({ kind: null, product: comparisons })
  }, [comparisons, isComparisonSuccess, kindId, setParams])

  // get list of comparable kinds
  const { data: kinds, isSuccess: isKindsSuccess } = useQuery({
    queryKey: kindKeys.list({ product: comparisons }),
    queryFn: () => loadKinds(comparisons),
    enabled: isComparisonSuccess, // comparisons are empty until loaded, and the backend lists all kinds for none
  })

  // if nothing is passed, redirect to first comparable kind
  useEffect(() => {
    if (isComparisonSuccess && comparisons.length > 0 && isKindsSuccess && kinds.length > 0 && kindId === null && productIds.length === 0)
      setParams({ kind: kinds[0].id })
  }, [isKindsSuccess, kinds, kindId, productIds, isComparisonSuccess, comparisons, setParams])

  // if product list is passed compare them, once all of them are loaded
  const products = useQueries({
    queries: productIds.map((productId) => ({
      queryKey: productKeys.detail(productId),
      queryFn: () => loadProduct(productId),
    })),
    combine: (results) => results.every((result) => result.isSuccess) ? results.map((result) => result.data) : undefined,
  })

  const currentKind = products?.[0]?.kind?.[0] ?? kindId

  const { data: kind, isSuccess: isKindSuccess } = useQuery({
    queryKey: kindKeys.detail(currentKind ?? 0),
    queryFn: () => loadKind(currentKind!),
    enabled: currentKind !== null
  })

  const { data: fields } = useQuery({
    queryKey: productKeys.fields(),
    queryFn: () => getProductFields()
  })

  // field names come with units after a comma
  const fieldNames = useMemo(() => {
    const names: Record<string, string[]> = {}
    if (fields !== undefined) {
      Object.keys(fields).forEach((key) => {
        const name = fields[key].split(',')
        if (name.length === 1)
          name.push('')
        names[key] = name
      })
    }
    return names
  }, [fields])

  const productFields = !(isKindSuccess && products !== undefined && products.length > 0) ? [] :
    kind.comparison.reduce((fields, name) => {
      const field = name as keyof Product
      const value = products[0][field]
      const differ = !deepCompare(...products.map((product) => product[field]))
      if (differ || (!different && value !== undefined && value !== ''))
        fields.push({
          field,
          differ
        })
      return fields
    }, [] as { field: keyof Product, differ: boolean }[])

  const uncompareProduct = (productId: number) => {
    uncompare(productId, () => {
      setParams({ product: productIds.filter((id) => id !== productId) })
    })
  }

  const handleCartClick = (product: Product) => {
    if (!product.variations)
      addItem(product)
  }

  if (isComparisonSuccess && productIds.length === 0 && kindId === null && comparisons.length === 0)
    return (
      <Alert variant="danger" className="mb-4">Отсутствуют товары для сравнения</Alert>
    )

  if (kindId !== null || products === undefined || !isKindsSuccess)
    return (
      <PageLoading />
    )

  return (
    <>
      {kinds.length > 1 ? (
        <div className="mb-12 inline-flex" role="group">
          {kinds.map((kind, index) => (
            <Link
              className={`${buttonClass({ variant: kind.id === currentKind ? 'dark' : 'secondary', size: 'lg' })} ${index > 0 ? '-ms-px rounded-s-none' : ''} ${index < kinds.length - 1 ? 'rounded-e-none' : ''}`}
              href={`/compare/?kind=${kind.id}`}
              aria-current={kind.id === currentKind ? 'page' : undefined}
              key={kind.id}>
              {kind.name}
            </Link>
          ))}
        </div>
      ) : (
        <h2 className="mb-3 pb-4 text-h3">{isKindSuccess ? kind.name : "Товары"}</h2>
      )}

      {products.length === 1 && (
        <Alert variant="secondary" className="mb-12">Добавьте ещё как минимум один товар в сравнение</Alert>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[45rem] table-fixed align-top text-sm">
          <thead>
            <tr className="border-b border-[#bccad9] align-bottom">
              <td className={`${cellClass} align-middle`}>
                <div className={checkClass()}>
                  <input className={checkInputClass()} type="checkbox" id="differences" checked={different} onChange={() => setDifferent(!different)} />
                  <label className={checkLabelClass} htmlFor="differences">Только различия</label>
                </div>
              </td>
              {products.map((product) => (
                <td className="border px-6 pt-3 pb-6 text-center" key={product.id}>
                  <button type="button" className={`${buttonClass({ variant: 'link-danger', size: 'sm', block: true })} mb-2`} onClick={() => uncompareProduct(product.id)}>
                    <IconTrash size={14} stroke={1.5} className="me-1" />Удалить
                  </button>
                  <Link
                    className="relative mb-4 inline-block size-20"
                    href={`/products/${product.code}`}>
                    {product.image ? (
                      <Image
                        src={product.image}
                        fill
                        style={{ objectFit: 'contain' }}
                        sizes="80px"
                        alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
                    ) : (
                      <NoImage size={80} />
                    )}
                  </Link>
                  <h3 className="mb-3 text-sm leading-[1.2] font-medium">
                    <Link className="text-heading hover:text-primary" href={`/products/${product.code}`}>
                      {product.title}
                    </Link>
                  </h3>
                  {product.enabled && product.instock > 0 && (
                    <button type="button" className={buttonClass({ variant: 'success', size: 'sm' })} onClick={() => handleCartClick(product)} disabled={addingProductId === product.id}>
                      {product.variations ? "Выбрать" : "Купить"}
                      {addingProductId === product.id && <ButtonLoading />}
                    </button>
                  )}
                </td>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.keys(fieldNames).length > 0 && productFields.length > 0 && productFields.map(({ field, differ }) => (
              <tr className={(differ && !different) ? "bg-[color-mix(in_srgb,var(--color-danger)_10%,white)]" : ""} key={field}>
                <th className={headerCellClass}>
                  {fieldNames[field][0]}
                  <FieldHelp field={field} />
                </th>
                {products.map((product) => (
                  <td className={cellClass} key={product.id}>
                    {product[field] && (
                      <>
                        {prettifyProductFieldValue(field, product[field])}
                        {fieldNames[field][1]}
                      </>
                    )}
                  </td>
                ))}
              </tr>
            ))}
            <tr>
              <th className={headerCellClass}>Цена</th>
              {products.map((product) => (
                <td className={cellClass} key={product.id}>
                  {product.enabled && product.price > 0 && <ProductPrice product={product} delFs="xs" />}
                </td>
              ))}
            </tr>
            { /*
            <tr>
              <th class="text-dark">Рейтинг</th>
              {% for product in products %}
              <td>
              {% if product.allow_reviews %}
              {% get_rating for product as product_rating %}
              {% if product_rating %}
              {{ product_rating|prettify }}/5
              {% endif %}
              {% endif %}
              </td>
              {% endfor %}
            </tr>
            */
            }
            {productFields.length > 5 && (
              <tr>
                <th className={headerCellClass}></th>
                {products.map((product) => (
                  <td className={cellClass} key={product.id}>
                    {product.instock > 0 && (
                      <button type="button" className={buttonClass({ variant: 'success', block: true })} onClick={() => handleCartClick(product)} disabled={addingProductId === product.id}>
                        {product.variations ? "Выбрать" : "Купить"}
                        {addingProductId === product.id && <ButtonLoading />}
                      </button>
                    )}
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}
