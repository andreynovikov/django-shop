'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useQuery, useQueries } from '@tanstack/react-query'
import { useQueryStates, parseAsInteger, parseAsNativeArrayOf } from 'nuqs'

import { IconTrashX } from '@tabler/icons-react'

import FieldHelp from '@/components/product/field-help'
import NoImage from '@/components/product/no-image'
import { PageLoading } from '@/components/loading'
import { buttonClass } from '@/components/ui/button'

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

const cellClass = 'border border-gray-200 p-2'

// Reading the query needs a Suspense boundary, the page is static
export default function ProductComparison() {
  const [{ kind: kindId, product: productIds }, setParams] = useQueryStates(comparisonParams)

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

  if (isComparisonSuccess && productIds.length === 0 && kindId === null && comparisons.length === 0)
    return (
      <div className="mb-4 border border-red-200 bg-red-50 p-4 text-red-800" role="alert">Отсутствуют товары для сравнения</div>
    )

  if (kindId !== null || products === undefined || !isKindsSuccess)
    return (
      <PageLoading />
    )

  return (
    <>
      {kinds.length > 1 ? (
        <div className="mb-12 inline-flex flex-wrap" role="group">
          {kinds.map((kind) => (
            <Link className={buttonClass({ variant: kind.id === currentKind ? 'dark' : 'secondary', size: 'lg' })} href={`/compare/?kind=${kind.id}`} key={kind.id}>
              {kind.name}
            </Link>
          ))}
        </div>
      ) : (
        <h2 className="mb-2 pb-4 text-[1.8rem] leading-[1.1] font-bold">{isKindSuccess ? kind.name : "Товары"}</h2>
      )}

      {products.length === 1 && (
        <div className="mb-12 border border-gray-300 bg-gray-200 p-4 text-gray-700" role="alert">Добавьте ещё как минимум один товар в сравнение</div>
      )}

      <div className="overflow-x-auto">
        <table className="mb-4 w-full table-fixed text-xs" style={{ minWidth: "45rem" }} id="comparison">
          <thead>
            <tr>
              <td className={`${cellClass} align-middle`}>
                <div className="ps-6">
                  <input className="float-start -ms-6 mt-px size-4 accent-dark" type="checkbox" id="differences" checked={different} onChange={() => setDifferent(!different)} />
                  <label htmlFor="differences">Только различия</label>
                </div>
              </td>
              {products.map((product) => (
                <td className={`${cellClass} px-6 pb-6 text-center align-top`} key={product.id}>
                  <button type="button" className={`${buttonClass({ variant: 'link-danger', size: 'sm', block: true })} mb-2`} onClick={() => uncompareProduct(product.id)}>
                    <IconTrashX className="me-1" />Удалить
                  </button>
                  <Link
                    className="relative mb-4 inline-block"
                    style={{ width: 80, height: 80 }}
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
                  <h3 className="mb-2 text-xs leading-[1.1] font-bold">
                    <Link href={`/products/${product.code}`}>
                      {product.title}
                    </Link>
                  </h3>
                </td>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.keys(fieldNames).length > 0 && productFields.length > 0 && productFields.map(({ field, differ }) => (
              <tr className={(differ && !different) ? "bg-red-100" : ""} key={field}>
                <th className={`${cellClass} text-start align-top text-dark first-letter:uppercase`}>
                  {fieldNames[field][0]}
                  <FieldHelp field={field} />
                </th>
                {products.map((product) => (
                  <td className={`${cellClass} backend-content align-top`} key={product.id}>
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
          </tbody>
        </table>
      </div>
    </>
  )
}
