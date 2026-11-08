import { cache } from 'react'
import { Metadata } from 'next/types'

import FieldHelp from '@/components/product/field-help'
import ImageCarousel from '@/components/product/image-carousel'
import NoImage from '@/components/product/no-image'
import ProductCompareButton from '@/components/product/compare-button'
import ProductRatingLink from '@/components/product/rating-link'
import ProductReviews from '@/components/product/reviews'
import ProductRibbons from '@/components/product/ribbons'
import { ProductTab, ProductTabs, ProductTabsProvider } from '@/components/product/tabs'

import { prettifyProductFieldValue } from '@/lib/format'
import { rows } from '@/lib/partition'
import { getProductFields, loadProducts } from '@/lib/queries'
import { Product } from '@/lib/types'

import { getProduct } from './load'

export const revalidate = 86400 // once a day

const fieldList: (keyof Product)[] = [
  'km_class', 'km_font', 'km_needles', 'km_prog', 'km_rapport',
  'sw_hoopsize', 'sw_datalink', 'sm_software', 'sm_shuttletype', 'sm_stitchwidth',
  'sm_stitchlenght', 'sm_maxi', 'sm_stitchquantity', 'sm_buttonhole', 'sm_alphabet',
  'sm_dualtransporter', 'sm_platformlenght', 'sm_freearm', 'sm_feedwidth',
  'sm_footheight', 'sm_constant', 'sm_speedcontrol', 'sm_needleupdown', 'sm_threader',
  'sm_autocutter', 'sm_spool', 'sm_presscontrol', 'sm_power', 'sm_light', 'sm_organizer',
  'sm_autostop', 'sm_ruler', 'sm_wastebin', 'sm_cover', 'sm_display', 'sm_advisor',
  'sm_memory', 'sm_mirror', 'sm_startstop', 'sm_kneelift', 'sm_diffeed',
  'sm_easythreading', 'ov_freearm', 'sm_needles', 'prom_transporter_type',
  'prom_shuttle_type', 'prom_speed', 'prom_needle_type', 'prom_stitch_lenght',
  'prom_foot_lift', 'prom_fabric_type', 'prom_oil_type', 'weight', 'prom_weight',
  'prom_cutting', 'prom_threads_num', 'prom_power', 'prom_bhlenght',
  'prom_overstitch_lenght', 'prom_overstitch_width', 'prom_stitch_width',
  'prom_needle_width', 'prom_needle_num', 'prom_platform_type', 'prom_button_diaouter',
  'prom_button_diainner', 'prom_needle_height', 'prom_stitch_type', 'prom_autothread',
  'developer_country', 'country', 'warranty'
]

function filterProductFields(product: Product) {
  return fieldList.filter(field => {
    if (!(field in product))
      return false
    if (field === 'country' || field === 'developer_country')
      return product[field].enabled
    return product[field]
  })
}

// Descriptions are written for the wider columns and the headings of the main site
function rebootstrap(value: string) {
  value = value.replaceAll('col-md-8', 'col-md-4')
  value = value.replaceAll('col-md-10', 'col-md-5')
  value = value.replaceAll('col-md-12', 'col-md-6')
  value = value.replaceAll('<h3>', '<h5>')
  value = value.replaceAll('</h3>', '</h5>')
  value = value.replaceAll('<h4>', '<h6>')
  value = value.replaceAll('</h4>', '</h6>')
  value = value.replaceAll('embed-responsive embed-responsive-4by3', 'ratio ratio-4x3')
  value = value.replaceAll('embed-responsive embed-responsive-16by9', 'ratio ratio-16x9')
  return value
}

// Field names are "name,unit"
const getFieldNames = cache(async () => {
  const fields = await getProductFields()
  return Object.entries(fields).reduce((names, [key, value]) => {
    const name = value.split(',')
    if (name.length === 1)
      name.push('')
    names[key] = name
    return names
  }, {} as Record<string, Array<string>>)
})

export async function generateMetadata({ params }: PageProps<'/products/[code]'>): Promise<Metadata> {
  const { code } = await params
  const product = await getProduct(code)

  return {
    title: product.title,
  }
}

export default async function ProductPage({ params }: PageProps<'/products/[code]'>) {
  const { code } = await params
  const [product, fieldNames] = await Promise.all([getProduct(code), getFieldNames()])

  const productFields = filterProductFields(product)

  const tabs: ProductTab[] = []
  if (product.descr)
    tabs.push({
      value: 'description',
      label: 'Описание',
      content: (
        <>
          <div className="backend-content pb-4 md:mb-4" itemProp="description" dangerouslySetInnerHTML={{ __html: rebootstrap(product.descr) }} />
          {product.spec && <div className="backend-content pb-4 md:mb-4" dangerouslySetInnerHTML={{ __html: rebootstrap(product.spec) }} />}
        </>
      )
    })
  if (product.manuals)
    tabs.push({
      value: 'manuals',
      label: 'Инструкция',
      content: <div className="backend-content" dangerouslySetInnerHTML={{ __html: product.manuals.replaceAll('/static', '') }} />
    })
  if (product.complect)
    tabs.push({
      value: 'complect',
      label: 'Комплектация',
      content: <div className="backend-content" dangerouslySetInnerHTML={{ __html: product.complect }} />
    })
  if (product.stitches)
    tabs.push({
      value: 'stitches',
      label: 'Строчки',
      content: <div className="backend-content" dangerouslySetInnerHTML={{ __html: product.stitches }} />
    })
  if (Object.keys(fieldNames).length > 0 && productFields.length > 0)
    tabs.push({
      value: 'specification',
      label: 'Технические характеристики',
      content: (
        <>
        <div className="grid items-start gap-x-6 lg:grid-cols-2">
          {rows(productFields, 2).map((row, index) => (
            <table className="mb-4 w-full text-xs" key={index}>
              <tbody>
                {row.map((field) => (
                  <tr className="border-b border-gray-200 last:border-b-0" key={field}>
                    <th className="p-2 text-start align-top font-normal tracking-widest uppercase">
                      {fieldNames[field][0]}
                      <FieldHelp field={field} />
                    </th>
                    <td className="p-2 align-top text-muted">
                      {prettifyProductFieldValue(field, product[field])}
                      {fieldNames[field][1]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ))}
        </div>
        {product.certificate && (
          <div className="pb-3 mb-md-3">
            {product.certificate.startsWith('http') ? (
              <a href={product.certificate} target="_blank">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/i/fgis-icon.svg" alt="" width="20" className="mx-1 ratio-1x1 align-text-bottom" />
                Сертификат соответствия требованиям технического регламента
              </a>
            ) : (
              <>{product.certificate}</>
            )}
          </div>
        )}
        </>
      )
    })
  if (product.allow_reviews)
    tabs.push({
      value: 'reviews',
      label: 'Отзывы',
      content: <ProductReviews productId={product.id} />
    })

  return (
    <ProductTabsProvider defaultTab={tabs[0]?.value ?? ''}>
      <div itemScope itemType="http://schema.org/Product">
        <section className="container grid gap-x-6 py-4 lg:grid-cols-[7fr_5fr]">
          <div className="relative order-2 min-w-0 lg:order-1">
            <ProductRibbons product={product} detail />
            {product.image ? (
              <ImageCarousel image={product.image} images={product.images} />
            ) : (
              <div className="hidden lg:block">
                <NoImage size={300} block />
              </div>
            )}
          </div>

          <div className="order-1 min-w-0 lg:order-2">
            <h1 className="mb-4 text-4xl leading-[1.1] tracking-widest uppercase lg:text-[3.5rem]" itemProp="name">{product.title}</h1>
            <div itemProp="offers" itemScope itemType="http://schema.org/Offer">
              <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-end">
                {product.allow_reviews && <ProductRatingLink product={product.id} />}
              </div>
            </div>
            {product.partnumber && <p className="mb-6 text-muted">Код производителя: {product.partnumber}</p>}
            {(product.runame || product.whatis) && <p className="mb-6 text-muted">{product.whatis} {product.runame}</p>}

            {product.kind && (
              <div className="mb-4">
                <ProductCompareButton productId={product.id} kind={product.kind[0]} />
              </div>
            )}
          </div>
        </section>

        <section className="container mt-12">
          <ProductTabs tabs={tabs} />
        </section>
      </div>
    </ProductTabsProvider>
  )
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const products = await loadProducts(null, 1000, {}, '')
  return products.results.map((product) => ({ code: product.code }))
}
