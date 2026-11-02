import { cache } from 'react'
import { Metadata } from 'next/types'
import { notFound } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'

import { Menu } from '@base-ui/react/menu'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductImpression from '@/components/product/ecommerce'
import FieldHelp from '@/components/product/field-help'
import NoImage from '@/components/product/no-image'
import ProductMiniCard from '@/components/product/mini-card'
import ProductPrice from '@/components/product/price'
import ProductRating from '@/components/product/rating'
import ProductUserActions from '@/components/product/user-actions'
import ProductShopping from '@/components/product/shopping'
import ProductPreorder from '@/components/product/preorder'
import RelatedProductsCarousel from '@/components/product/related'
import ProductStockWrapper from '@/components/product/stock-wrapper'
import ProductReviewsWrapper from '@/components/product/reviews-wrapper'
import ImageCarousel from '@/components/product/image-carousel'

import { baseFilters } from '@/lib/catalog'
import { prettifyProductFieldValue } from '@/lib/format'
import { loadProducts, loadProductByCode, getProductFields, loadCurrentSite, loadCategories, HttpError } from '@/lib/queries'
import { Product, PaginatedResult } from '@/lib/types'

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

const categoryPathname = (path: string[]) => `/catalog/${path.join('/')}/`

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

// Shared by generateMetadata and the page, so the store is fetched once per render
const getProduct = cache(async (code: string) => {
  try {
    return await loadProductByCode(code)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

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

  const category = product.categories
    .filter(category => !['New', 'promo', 'Discount'].includes(category.slug)) // skip special categories
    .sort((a, b) => b.path.breadcrumbs.length - a.path.breadcrumbs.length)[0] // get the longest path

  const breadcrumbs = category ? [
    ...category.path.breadcrumbs.map((breadcrumb, index, parents) => ({
      label: breadcrumb.name,
      href: categoryPathname(parents.slice(0, index + 1).map(({ slug }) => slug)),
    })),
  ] : []

  return pageContentWrapper({
    title: product.title,
    titleAddon: <>
      {(product.runame || product.whatis) && (
        <span className="text-white opacity-70">
          <span>{product.whatis}</span>
          <span className="d-none d-sm-inline"> {product.runame}</span>
        </span>
      )}
      {product.allow_reviews && <ProductRating product={product.id} anchor="reviews" />}
    </>,
    breadcrumbs,
    dark: true,
    overlapped: true,
    children: (
      <>
        <div className="container" itemScope itemType="https://schema.org/Product">
          <ProductImpression product={product} />
          <meta itemProp="name" content={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
          {product.article && <meta itemProp="sku" content={product.article} />}
          {product.image && <meta itemProp="image" content={product.image} />}
          <div className="bg-light shadow-lg rounded-3 px-4 py-3 mb-5">
            <div className="px-lg-3">
              <div className="row">
                <div className="col-lg-7 pe-lg-0">
                  {product.image ? (
                    <div className="d-block text-center">
                      <ImageCarousel
                        image={product.big_image ?? product.image}
                        images={product.images}
                        alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
                    </div>
                  ) : (
                    <div className="d-none d-lg-block">
                      <NoImage size={300} block />
                    </div>
                  )}
                </div>
                <div className="col-lg-5 pt-4 pt-lg-0">
                  <div className="product-details ms-auto pb-3" itemProp="offers" itemScope itemType="https://schema.org/Offer">
                    <link itemProp="url" href={site.url_prefix + `/products/${code}/`} />
                    {product.enabled && product.cost > 0 && (
                      <div className="d-flex flex-row xalign-items-baseline mb-3">
                        <div className="h3 fw-normal text-accent flex-shrink-1">
                          <ProductPrice product={product} delFs="lg" microdata />
                        </div>
                        <div className="ms-3 text-end w-100">
                          {product.discount > 0 && (
                            <span className="badge bg-primary badge-shadow ms-2 mb-2">Скидка</span>
                          )}
                          {product.isnew && (
                            <span className="badge bg-info badge-shadow ms-2 mb-2">Новинка</span>
                          )}
                          {product.recomended && (
                            <span className="badge bg-warning badge-shadow ms-2 mb-2">Рекомендуем</span>
                          )}
                          {product.sales && product.sales.filter((action) => !!action.notice && !!!action.brief).map((action) => (
                            <span className="badge bg-danger badge-shadow ms-2 mb-2" key={action.id}>{action.notice}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="position-relative me-n4">
                      <link itemProp="availability" href={`https://schema.org/${product.enabled ? product.instock > 1 ? 'InStock' : 'OutOfStock' : 'Discontinued'}`} />
                      <div className={`product-badge product-${product.instock < 1 ? "not-" : ""}available mt-${product.enabled ? "1" : "3"}`}>
                        <i className={`ci-security-${product.instock > 1 ? "check" : product.instock === 1 ? "announcement" : "close"}`} />
                        {product.enabled ? (
                          product.instock > 1 ? "В наличии" : product.instock === 1 ? "Осталось мало" : "Закончились"
                        ) : (
                          "Товар снят с продажи"
                        )}
                      </div>
                    </div>
                    {product.enabled && (
                      <>
                        <div className="me-2">
                          <div className="me-5 pb-4 pe-5 fs-sm">
                            {product.sales && (
                              product.sales.filter((action) => !!action.brief).map((action) => (
                                <div className="mb-2" key={action.id}>
                                  <i className="ci-gift text-danger pe-2" />
                                  <span dangerouslySetInnerHTML={{ __html: renderTemplate(action.brief, product) }}></span>
                                </div>
                              ))
                            )}
                            {product.state && (
                              <div className="mb-2">
                                <i className="ci-message text-danger pe-2" />
                                {product.state}
                              </div>
                            )}
                            {product.sales_notes && (
                              <div className="mb-2">
                                <i className="ci-announcement text-danger pe-2" />
                                {product.sales_notes}
                              </div>
                            )}
                          </div>
                        </div>
                        {product.cost > 0 ? (
                          <div className="pt-2 pb-4">
                            {product.instock > 0 ? (
                              <ProductShopping product={product} />
                            ) : (
                              <ProductPreorder product={product} />
                            )}
                          </div>
                        ) : (
                          <div className="py-5"></div>
                        )}
                      </>
                    )}
                    {(product.enabled || product.kind) && <ProductUserActions product={product} />}

                    {product.enabled && product.cost > 0 && (
                      <div className="mb-4">
                        <Menu.Root modal={false}>
                          <Menu.Trigger className="btn btn-outline-secondary btn-sm w-100">
                            <i className="ci-location text-muted lead align-middle mt-n1 me-2" />Наличие в магазинах
                          </Menu.Trigger>
                          <Menu.Portal>
                            <Menu.Positioner sideOffset={3} align="end" collisionAvoidance={{ side: 'none' }}>
                              <Menu.Popup className="card" style={{ width: "var(--anchor-width)" }}>
                                <div className="card-body">
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
                        <div className="mb-4 mx-auto w-75">
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
            <div className="pb-3 mb-md-3" itemProp="description" dangerouslySetInnerHTML={{ __html: product.descr }} />
          )}

          {product.constituents && (
            <div className="pt-lg-2 pb-3 mb-md-3">
              <h2 className="h3 pb-2">Состав комплекта</h2>
              <div className="container px-0 mx-n2 d-flex flex-wrap">
                {product.constituents.map((item) => (
                  <div className="card m-2" style={{ maxWidth: "230px" }} key={item.id}>
                    {item.image ? (
                      <div className=" card-img-top px-3">
                        <div className="position-relative" style={{ aspectRatio: 1 }}>
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
                    <div className="card-body fs-sm">
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
            <div className="pb-3 mb-md-3" dangerouslySetInnerHTML={{ __html: product.spec }} />
          )}

          {Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
            <div className="pt-lg-2 pb-3 mb-md-3">
              <div className="h3 d-flex align-items-end pb-2">
                <h2 className="h3 m-0 p-0 flex-grow-1">Характеристики</h2>
                {product.manufacturer?.logo && (
                  <div className="flex-shrink-1" itemProp="brand" itemScope itemType="https://schema.org/Brand">
                    <meta itemProp="name" content={product.manufacturer.name} />
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img alt={product.manufacturer.name} src={product.manufacturer.logo} className="sw-product-logo" />
                  </div>
                )}
              </div>
              <div className="product-spec container fs-sm">
                {productFields.map((field) => (
                  <div className="row mb-2" key={field}>
                    {field === 'fabric_verylite' ? (
                      <>
                        <span className="col-md px-0 text-muted">
                          <span className="d-block border-bottom">
                            <span>
                              Диапазон прошиваемых материалов{" "}
                              <Link href="/blog/H/">
                                <i className="ci-message fs-ms text-muted" />
                              </Link>
                            </span>
                          </span>
                        </span>
                        <span className="col-md pt-1 pt-sm-0 pe-0 ps-2 align-self-end">
                          Очень легкие – {product.fabric_verylite}<br />
                          Легкие – {product.fabric_lite}<br />
                          Средние и умеренно тяжелые – {product.fabric_medium}<br />
                          Тяжелые – {product.fabric_hard}<br />
                          Трикотаж – {product.fabric_stretch}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="col-md px-0 text-muted">
                          <span className="d-block border-bottom">
                            {fieldNames[field][0]}
                            <FieldHelp field={field} />
                          </span>
                        </span>
                        <span className="col-md pt-1 pt-sm-0 pe-0 ps-2 align-self-end">
                          {prettifyProductFieldValue(field, product[field])}
                          {fieldNames[field][1]}
                        </span>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {product.stitches && (
            <div className="pt-lg-2 pb-3 mb-md-3">
              <h2 className="h3 pb-2">Строчки {product.title}</h2>
              <div dangerouslySetInnerHTML={{ __html: product.stitches }} />
            </div>
          )}

          {product.complect && (
            <div className="pt-lg-2 pb-3 mb-md-3">
              <h2 className="h3 pb-2">Комплектация</h2>
              <div dangerouslySetInnerHTML={{ __html: product.complect }} />
            </div>
          )}

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

          {product.manuals && (
            <div className="pt-lg-2 pb-3 mb-md-3">
              <h2 className="h3 pb-2">Инструкции {product.title}</h2>
              <div dangerouslySetInnerHTML={{ __html: product.manuals }} />
            </div>
          )}
        </div>

        {(product.accessories || product.similar) && (
          <div className="border-top pt-5">
            {product.accessories && (
              <div className="container pt-lg-2 pb-5 mb-md-3">
                <RelatedProductsCarousel product={product} related={product.accessories} title="Популярные аксессуары для" />
              </div>
            )}
            {product.similar && (
              <div className="container pt-lg-2 pb-5 mb-md-3">
                <RelatedProductsCarousel product={product} related={product.similar} title="Товары похожие на" />
              </div>
            )}
          </div>
        )}

        {product.dealertxt && (
          <div className="border-top pt-5">
            <div className="container pt-lg-2 pb-5 mb-md-3">
              <h2 className="h3 text-center pb-4">Обратите внимание!</h2>
              <div dangerouslySetInnerHTML={{ __html: product.dealertxt }} />
            </div>
          </div>
        )}

        <ProductReviewsWrapper product={product} />
      </>
    )
  })
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
