import { cache } from 'react'
import { Metadata } from 'next/types'
import Image from 'next/image'

import ProductImpression from '@/components/product/ecommerce'
import BuyButton from '@/components/product/buy-button'
import FieldHelp from '@/components/product/field-help'
import NoImage from '@/components/product/no-image'
import { ProductImageGallery, GalleryLink } from '@/components/product/image-gallery'
import { badgeClass } from '@/components/ui/badge'
import { buttonClass } from '@/components/ui/button'

import { prettifyProductFieldValue } from '@/lib/format'
import { loadProducts, getProductFields } from '@/lib/queries'
import { Product } from '@/lib/types'

import { getProduct } from './load'

export const revalidate = 86400 // once a day

const sectionTitleClass = 'mt-2.5 mb-2 text-3xl leading-none font-light'

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

  // the main image is the first slide, the other images follow it. The backend leaves out an empty list.
  const images = product.images ?? []
  const mainImage = product.big_image ?? product.image
  const slides = [...(mainImage ? [{ src: mainImage }] : []), ...images]
  const firstImageSlide = mainImage ? 1 : 0

  return (
    <ProductImageGallery slides={slides}>
      <div itemScope itemType="http://schema.org/Product">
        <ProductImpression product={product} />
        <h1 className="mt-2.5 mb-5 text-4xl leading-none font-light text-primary uppercase" itemProp="name">
          {product.title}
          <sup className="mt-6 block sm:mt-0 sm:inline">
            {product.isnew && <span className={`${badgeClass({ size: 'sm' })} ms-1 bg-danger text-white`}>Новинка</span>}
            {product.recomended && <span className={`${badgeClass({ size: 'sm' })} ms-1 bg-success text-white`}>Рекомендуем</span>}
          </sup>
        </h1>

        {product.partnumber && <p className="mb-4">Код производителя: {product.partnumber}</p>}
        {(product.runame || product.whatis) && <p className="mb-4">{product.whatis} {product.runame}</p>}

        <div className="flex flex-col-reverse sm:flex-row" style={{ gap: 10 }}>
          <div className="grow">
            {product.image ? (
              <div className="text-center">
                <GalleryLink index={0} className="me-1">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    className="xsi-product-image mx-auto"
                    src={product.image}
                    alt={`${product.title} ${product.whatis}`}
                    itemProp="image" />
                </GalleryLink>
              </div>
            ) : (
              <NoImage size={160} className="mx-auto hidden! lg:block!" />
            )}
          </div>

          <div className="self-stretch rounded-md border border-black/15 bg-white sm:self-start">
            <div className="p-4">
              {product.enabled ? (
                <div itemProp="offers" itemScope itemType="http://schema.org/Offer">
                  {product.discount > 0 && (
                    <p className="oldprice mb-4">
                      <del>{product.price.toLocaleString('ru')}&nbsp;руб.</del>
                    </p>
                  )}
                  <div>
                    <span className="align-middle text-base font-bold">
                      <span className="text-xl font-bold" itemProp="price">{product.cost.toLocaleString('ru')}</span>&nbsp;руб.
                    </span>

                    <BuyButton product={product} className={`${buttonClass()} ms-2 font-bold`} />

                    {product.wb_link && <div className="mt-2">
                      <a href={product.wb_link} className={`${buttonClass({ variant: 'wb' })} font-bold`} role="button">
                        Купить на WB
                      </a>
                    </div>}
                    {product.ozon_link && <div className="mt-2">
                      <a href={product.ozon_link} className={`${buttonClass({ variant: 'ozon' })} font-bold`} role="button">
                        Купить на Ozon
                      </a>
                    </div>}

                    <span itemProp="priceCurrency" className="hidden">RUB</span>
                  </div>

                  <div className="mt-4">
                    <span className="product-nal-caption">Наличие:</span>{" "}
                    {product.instock > 1 ? (
                      <span className="product-nal-true">Есть</span>
                    ) : product.instock == 1 ? (
                      <span className="product-nal-true">Мало</span>
                    ) : (
                      <span className="product-nal-false">Нет</span>
                    )}
                  </div>

                  {product.sales_notes && <p className="my-4">{product.sales_notes}</p>}
                </div>
              ) : (
                <span className="product-nal-false">Товар снят с продажи</span>
              )}
            </div>
          </div>
        </div>

        <div className="mt-2">
          {images.map((image, index) => (
            <GalleryLink index={index + firstImageSlide} className="me-1" key={index}>
              <span className="relative inline-block" style={{ width: 80, height: 80 }}>
                <Image
                  src={image.src}
                  fill
                  style={{ objectFit: 'contain' }}
                  sizes="80px"
                  loading="lazy"
                  alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title} - фото №${index + 2}`} />
              </span>
            </GalleryLink>
          ))}
        </div>

        <div className="mt-4" />

        {product.descr && (
          <div className="backend-content pb-4" itemProp="description" dangerouslySetInnerHTML={{ __html: rebootstrap(product.descr) }} />
        )}
        {product.spec && (
          <div className="backend-content pb-4" dangerouslySetInnerHTML={{ __html: rebootstrap(product.spec) }} />
        )}

        {product.manuals && (
          <>
            <h2 className={sectionTitleClass}>Инструкции для {product.title}:</h2>
            <div className="backend-content pb-4" dangerouslySetInnerHTML={{ __html: product.manuals.replaceAll('/static', '') }} />
          </>
        )}

        {Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
          <>
            <h2 className={sectionTitleClass}>Характеристики{product.kind ? " " + product.title : ""}:</h2>
            <table className="mb-4 w-full">
              <tbody>
                {productFields.map((field, index) => (
                  <tr key={field}>
                    <th className={"p-2 text-start align-top font-normal" + (index === productFields.length - 1 ? "" : " border-b")}>
                      {fieldNames[field][0]}
                      <FieldHelp field={field} />
                    </th>
                    <td className={"p-2 align-top text-muted" + (index === productFields.length - 1 ? "" : " border-b")}>
                      {prettifyProductFieldValue(field, product[field])}
                      {fieldNames[field][1]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {product.stitches && (
          <>
            <h2 className={sectionTitleClass}>Строчки {product.title}:</h2>
            <div className="backend-content py-4" dangerouslySetInnerHTML={{ __html: product.stitches }} />
          </>
        )}

        {product.complect && (
          <>
            <h2 className={sectionTitleClass}>Комплектация{product.kind ? " " + product.title : ""}:</h2>
            <div className="backend-content py-4" dangerouslySetInnerHTML={{ __html: product.complect }} />
          </>
        )}

        {product.certificate && (
          <div className="pb-4">
            {product.certificate.startsWith('http') ? (
              <a href={product.certificate} target="_blank">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/i/fgis-icon.svg" alt="" width="20" className="mx-1 inline align-text-bottom" />
                Сертификат соответствия требованиям технического регламента
              </a>
            ) : (
              <>{product.certificate}</>
            )}
          </div>
        )}
      </div>
    </ProductImageGallery>
  )
}

// Machines and overlocks are prerendered, other products on their first visit
export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const products = await loadProducts(null, 1000, { kind: [1, 2] }, '', ['code'])
  return products.results.map((product) => ({ code: product.code }))
}
