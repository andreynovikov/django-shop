import { cache } from 'react'
import { Metadata } from 'next/types'
import Image from 'next/image'
import Link from 'next/link'

import { Menu } from '@base-ui/react/menu'
import { IconAlertCircle, IconGift, IconMapPin, IconMessageDots, IconShieldCheck, IconShieldExclamation, IconShieldX } from '@tabler/icons-react'

import ProductImpression from '@/components/product/ecommerce'
import FieldHelp from '@/components/product/field-help'
import NoImage from '@/components/product/no-image'
import ProductMiniCard from '@/components/product/mini-card'
import ProductPrice from '@/components/product/price'
import ProductUserActions from '@/components/product/user-actions'
import ProductShopping from '@/components/product/shopping'
import ProductPreorder from '@/components/product/preorder'
import RelatedProductsCarousel from '@/components/product/related'
import ProductStockWrapper from '@/components/product/stock-wrapper'
import ProductReviewsWrapper from '@/components/product/reviews-wrapper'
import ImageCarousel from '@/components/product/image-carousel'
import { badgeClass, badgeShadows } from '@/components/ui/badge'
import { buttonClass } from '@/components/ui/button'
import { cardBodyClass, cardClass } from '@/components/ui/card'
import { contentClass } from '@/components/ui/content'

import { baseFilters } from '@/lib/catalog'
import { prettifyProductFieldValue } from '@/lib/format'
import { loadProducts, getProductFields, loadCurrentSite, loadCategories } from '@/lib/queries'
import { Product, PaginatedResult } from '@/lib/types'

import { getProduct } from './load'

export const revalidate = 3600

// const gana = require('gana')

const fieldList: (keyof Product)[] = [
  'partnumber', 'manufacturer', 'article', 'developer_country', 'country', 'warranty',
  'fabric_verylite', 'km_class', 'km_font', 'km_needles', 'km_prog', 'km_rapport',
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
  'prom_button_diainner', 'prom_needle_height', 'prom_stitch_type', 'prom_autothread'
]

function filterProductFields(product: Product) {
  return fieldList.filter(field => {
    if (!(field in product))
      return false
    if (field === 'country' || field === 'developer_country')
      return product[field].enabled
    return product[field]
  })
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function renderTemplate(template: string, product: Product) {
  // const compileFn = gana(template)
  // return compileFn({ product })
  // TODO: find solution for templates
  return template
};

const getSite = cache(loadCurrentSite)

// A section below the product's main block and its title
const sectionClass = 'pb-4 md:mb-4 lg:pt-2'
const sectionTitleClass = 'mb-3 pb-2 text-h3'
// The specification: names above values below md, side by side from md up
const specNameClass = 'text-muted first-letter:uppercase'
const specValueClass = 'self-end ps-2 pt-1 sm:pt-0'
const noteIcon = { size: 16, stroke: 1.5, className: 'me-2 -mt-0.5 align-middle text-danger' }

// A tab sticking out of the right edge of the block, with a folded corner below it
function AvailabilityBadge({ product }: { product: Product }) {
  const available = product.instock >= 1
  const Icon = product.instock > 1 ? IconShieldCheck : product.instock === 1 ? IconShieldExclamation : IconShieldX
  return (
    <div className={`absolute top-1/2 -right-3 ${product.enabled ? 'mt-1' : 'mt-4'} flex -translate-y-1/2 items-center rounded-s-md py-[.425rem] ps-2.5 pe-4 text-ms after:pointer-events-none after:absolute after:right-1 after:-bottom-[.475rem] after:size-0 after:-rotate-45 after:border-[.525rem] after:border-transparent lg:-right-7 ${available ? 'bg-success text-white after:border-b-[#449d44]' : 'bg-secondary text-gray-700 after:border-b-[#d8deeb]'}`}>
      <Icon size="1.2em" stroke={1.5} className="me-1" />
      {product.enabled ? (
        product.instock > 1 ? "В наличии" : product.instock === 1 ? "Осталось мало" : "Закончились"
      ) : (
        "Товар снят с продажи"
      )}
    </div>
  )
}

const getFields = cache(async () => {
  const fields = await getProductFields()
  const fieldNames = Object.entries(fields).reduce((names, [key, value]) => {
    const name = value.split(',')
    if (name.length === 1)
      name.push('')
    names[key] = name
    return names
  }, {} as Record<string, Array<string>>)
  return {
    fields,
    fieldNames,
  }
})

export async function generateMetadata({ params }: PageProps<'/products/[code]'>): Promise<Metadata> {
  const { code } = await params
  const [product, site] = await Promise.all([getProduct(code), getSite()])

  const description = product.seodescr ?
    product.seodescr :
    `${product.title} ${product.partnumber ? product.partnumber + ' ' : ''}${product.manufacturer ? product.manufacturer.name + ' ' : ''}купите в Швейном Мире`

  return {
    title: product.title,
    description,
    alternates: {
      canonical: site.url_prefix + `/products/${code}/`,
    },
  }
}

export default async function ProductPage({ params }: PageProps<'/products/[code]'>) {
  const { code } = await params
  const [product, site] = await Promise.all([getProduct(code), getSite()])
  const { fieldNames } = await getFields()

  const productFields = filterProductFields(product)

  return (
    <>
      <div className="container" itemScope itemType="https://schema.org/Product">
        <ProductImpression product={product} />
        <meta itemProp="name" content={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
        {product.article && <meta itemProp="sku" content={product.article} />}
        {product.image && <meta itemProp="image" content={product.image} />}
        <div className="mb-12 rounded-lg bg-white px-6 py-4 shadow-lg">
          <div className="lg:px-4">
            <div className="grid lg:grid-cols-12 lg:gap-x-4">
              <div className="min-w-0 lg:col-span-7">
                {product.image ? (
                  <div className="block text-center">
                    <ImageCarousel
                      image={product.big_image ?? product.image}
                      images={product.images}
                      alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
                  </div>
                ) : (
                  <div className="hidden lg:block">
                    <NoImage size={300} block />
                  </div>
                )}
              </div>
              <div className="pt-6 lg:col-span-5 lg:pt-0">
                <div className="ms-auto pb-4 lg:w-full lg:max-w-[26rem] lg:pt-1" itemProp="offers" itemScope itemType="https://schema.org/Offer">
                  <link itemProp="url" href={site.url_prefix + `/products/${code}/`} />
                  {product.enabled && product.cost > 0 && (
                    <div className="mb-4 flex">
                      <div className="shrink text-h3 font-normal text-accent">
                        <ProductPrice product={product} delFs="lg" microdata />
                      </div>
                      <div className="ms-4 w-full text-end">
                        {product.discount > 0 && (
                          <span className={`${badgeClass()} ${badgeShadows.primary} ms-2 mb-2 bg-primary text-white`}>Скидка</span>
                        )}
                        {product.isnew && (
                          <span className={`${badgeClass()} ${badgeShadows.info} ms-2 mb-2 bg-info text-white`}>Новинка</span>
                        )}
                        {product.recomended && (
                          <span className={`${badgeClass()} ${badgeShadows.warning} ms-2 mb-2 bg-warning text-white`}>Рекомендуем</span>
                        )}
                        {product.sales && product.sales.filter((action) => !!action.notice && !!!action.brief).map((action) => (
                          <span className={`${badgeClass()} ${badgeShadows.danger} ms-2 mb-2 bg-danger text-white`} key={action.id}>{action.notice}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="relative -me-6">
                    <link itemProp="availability" href={`https://schema.org/${product.enabled ? product.instock > 1 ? 'InStock' : 'OutOfStock' : 'Discontinued'}`} />
                    <AvailabilityBadge product={product} />
                  </div>
                  {product.enabled && (
                    <>
                      <div className="me-2">
                        <div className="me-12 pe-12 pb-6 text-sm">
                          {product.sales && (
                            product.sales.filter((action) => !!action.brief).map((action) => (
                              <div className="mb-2" key={action.id}>
                                <IconGift {...noteIcon} />
                                <span dangerouslySetInnerHTML={{ __html: renderTemplate(action.brief, product) }}></span>
                              </div>
                            ))
                          )}
                          {product.state && (
                            <div className="mb-2">
                              <IconMessageDots {...noteIcon} />
                              {product.state}
                            </div>
                          )}
                          {product.sales_notes && (
                            <div className="mb-2">
                              <IconAlertCircle {...noteIcon} />
                              {product.sales_notes}
                            </div>
                          )}
                        </div>
                      </div>
                      {product.cost > 0 ? (
                        <div className="pt-2 pb-6">
                          {product.instock > 0 ? (
                            <ProductShopping product={product} />
                          ) : (
                            <ProductPreorder product={product} />
                          )}
                        </div>
                      ) : (
                        <div className="py-12"></div>
                      )}
                    </>
                  )}
                  {(product.enabled || product.kind) && <ProductUserActions product={product} />}

                  {product.enabled && product.cost > 0 && (
                    <div className="mb-6">
                      <Menu.Root modal={false}>
                        <Menu.Trigger className={buttonClass({ variant: 'outline-secondary', size: 'sm', block: true })}>
                          <IconMapPin size={20} stroke={1.5} className="me-2 text-muted" />Наличие в магазинах
                        </Menu.Trigger>
                        <Menu.Portal>
                          <Menu.Positioner sideOffset={3} align="end" collisionAvoidance={{ side: 'none' }} className="z-1000">
                            <Menu.Popup className={`${cardClass} w-(--anchor-width)`}>
                              <div className={cardBodyClass}>
                                <ProductStockWrapper id={product.id} />
                              </div>
                            </Menu.Popup>
                          </Menu.Positioner>
                        </Menu.Portal>
                      </Menu.Root>
                    </div>
                  )}

                  {product.enabled && product.gifts && (
                    <>
                      <div className="mb-1">Покупая {product.title} в интернет-магазине, Вы получите подарок:</div>
                      <div className="mx-auto mb-6 w-3/4">
                        {product.gifts.map((gift) => (
                          <ProductMiniCard product={gift} key={gift.id} />
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {product.descr && (
          <div className={`${contentClass()} pb-4 md:mb-4`} itemProp="description" dangerouslySetInnerHTML={{ __html: product.descr }} />
        )}

        {product.constituents && (
          <div className={sectionClass}>
            <h2 className={sectionTitleClass}>Состав комплекта</h2>
            <div className="-mx-2 flex flex-wrap">
              {product.constituents.map((item) => (
                <div className={`${cardClass} m-2 max-w-[230px]`} key={item.id}>
                  {item.image ? (
                    <div className="px-4">
                      <div className="relative aspect-square">
                        <Image
                          src={item.image}
                          fill
                          style={{ objectFit: "contain" }}
                          sizes="230px"
                          loading="lazy"
                          alt={`${item.whatis ? item.whatis + ' ' : ''}${item.title}`} />
                      </div>
                    </div>
                  ) : (
                    <div className="text-center">
                      <NoImage size={200} />
                    </div>
                  )}
                  <div className={`${cardBodyClass} text-sm`}>
                    <strong>
                      <Link className="text-muted" href={`/products/${item.code}`}>
                        {item.title}
                      </Link>
                      {/* TODO: there is no quantity in serializer output
                      item.quantity > 1 && (
                      <>({item.quantity} шт.)</>
                    ) */}
                    </strong>
                    {item.shortdescr && (
                      <> &mdash; {item.shortdescr}</>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {product.spec && (
          <div className={`${contentClass()} pb-4 md:mb-4`} dangerouslySetInnerHTML={{ __html: product.spec }} />
        )}

        {Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
          <div className={sectionClass}>
            <div className="mb-3 flex items-end pb-2 text-h3 text-heading">
              <h2 className="m-0 grow p-0 text-h3">Характеристики</h2>
              {product.manufacturer?.logo && (
                <div className="shrink" itemProp="brand" itemScope itemType="https://schema.org/Brand">
                  <meta itemProp="name" content={product.manufacturer.name} />
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img alt={product.manufacturer.name} src={product.manufacturer.logo} className="h-[30px] w-auto lg:h-[60px]" />
                </div>
              )}
            </div>
            <dl className="text-sm">
              {productFields.map((field) => (
                <div className="mb-2 grid md:grid-cols-2" key={field}>
                  {field === 'fabric_verylite' ? (
                    <>
                      <dt className={specNameClass}>
                        <span className="block border-b">
                          <span>
                            Диапазон прошиваемых материалов{" "}
                            <Link href="/blog/H/" aria-label="О диапазоне прошиваемых материалов">
                              <IconMessageDots size={14} stroke={1.5} className="align-[-2px] text-muted" />
                            </Link>
                          </span>
                        </span>
                      </dt>
                      <dd className={specValueClass}>
                        Очень легкие – {product.fabric_verylite}<br />
                        Легкие – {product.fabric_lite}<br />
                        Средние и умеренно тяжелые – {product.fabric_medium}<br />
                        Тяжелые – {product.fabric_hard}<br />
                        Трикотаж – {product.fabric_stretch}
                      </dd>
                    </>
                  ) : (
                    <>
                      <dt className={specNameClass}>
                        <span className="block border-b">
                          {fieldNames[field][0]}
                          <FieldHelp field={field} />
                        </span>
                      </dt>
                      <dd className={specValueClass}>
                        {prettifyProductFieldValue(field, product[field])}
                        {fieldNames[field][1]}
                      </dd>
                    </>
                  )}
                </div>
              ))}
            </dl>
          </div>
        )}

        {product.stitches && (
          <div className={sectionClass}>
            <h2 className={sectionTitleClass}>Строчки {product.title}</h2>
            <div className={contentClass()} dangerouslySetInnerHTML={{ __html: product.stitches }} />
          </div>
        )}

        {product.complect && (
          <div className={sectionClass}>
            <h2 className={sectionTitleClass}>Комплектация</h2>
            <div className={contentClass()} dangerouslySetInnerHTML={{ __html: product.complect }} />
          </div>
        )}

        {product.certificate && (
          <div className="pb-4 md:mb-4">
            {product.certificate.startsWith('http') ? (
              <a href={product.certificate} target="_blank">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/i/fgis-icon.svg" alt="" width="20" className="mx-1 inline aspect-square align-text-bottom" />
                Сертификат соответствия требованиям технического регламента
              </a>
            ) : (
              <>{product.certificate}</>
            )}
          </div>
        )}

        {product.manuals && (
          <div className={sectionClass}>
            <h2 className={sectionTitleClass}>Инструкции {product.title}</h2>
            <div className={contentClass()} dangerouslySetInnerHTML={{ __html: product.manuals }} />
          </div>
        )}
      </div>

      {(product.accessories || product.similar) && (
        <div className="border-t pt-12">
          {product.accessories && (
            <div className="container pb-12 md:mb-4 lg:pt-2">
              <RelatedProductsCarousel product={product} related={product.accessories} title="Популярные аксессуары для" />
            </div>
          )}
          {product.similar && (
            <div className="container pb-12 md:mb-4 lg:pt-2">
              <RelatedProductsCarousel product={product} related={product.similar} title="Товары похожие на" />
            </div>
          )}
        </div>
      )}

      {product.dealertxt && (
        <div className="border-t pt-12">
          <div className="container pb-12 md:mb-4 lg:pt-2">
            <h2 className="mb-3 pb-6 text-center text-h3">Обратите внимание!</h2>
            <div className={contentClass()} dangerouslySetInnerHTML={{ __html: product.dealertxt }} />
          </div>
        </div>
      )}

      <ProductReviewsWrapper product={product} />
    </>
  )
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const products = new Set()

  const categories = await loadCategories()

  const filters = {
    ...baseFilters,
    in_category: categories.map(category => category.id),
    variations: '',
  }
  const pageSize = 500
  const order = 'id'
  let currentPage = 1

  while (true) {
    const productsPage = await loadProducts(currentPage, pageSize, filters, order) as PaginatedResult<Product>
    productsPage.results.forEach(product => products.add(product.code))
    if (productsPage.totalPages <= currentPage)
      break
    currentPage++
  }

  return Array.from(products, code => ({ code }))
}
