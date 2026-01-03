import { useState, useEffect, Suspense, lazy } from 'react'
import { useRouter } from 'next/router'
import Image from 'next/image'
import Link from 'next/link'
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'
import { useInView } from 'react-intersection-observer'

import { Collapsible } from '@base-ui/react/collapsible'

import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Tooltip from 'react-bootstrap/Tooltip'

import PageLayout from '@/components/layout/page'
import FieldHelp from '@/components/product/field-help'
import NoImage from '@/components/product/no-image'
import ProductMiniCard from '@/components/product/mini-card'
import ProductPrice from '@/components/product/price'
import ProductRating from '@/components/product/rating'
import ProductShopping from '@/components/product/shopping'
import ProductPreorder from '@/components/product/preorder'
import ImageGallery from '@/components/product/image-gallery'
import ImageCarousel from '@/components/product/image-carousel'
import { Loading, PageLoading } from '@/components/loading'

import useFavorites from '@/lib/favorites'
import useComparison from '@/lib/comparison'
import { useSession } from '@/lib/session'
import { productKeys, loadProducts, loadProductByCode, getProductFields } from '@/lib/queries'
import { recomendedFilters, firstPageFilters } from '@/lib/catalog'
import { eCommerce } from '@/lib/ymec'

const ProductReviews = lazy(() => import('@/components/product/reviews'))
const ProductStock = lazy(() => import('@/components/product/stock'))

// const gana = require('gana')

const fieldList = [
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

const sliderSettings = {
  mouseDrag: true,
  items: 2,
  controls: true,
  nav: false,
  // autoHeight: true,
  controlsText: ['<i class="ci-arrow-left"></i>', '<i class="ci-arrow-right"></i>'],
  // navPosition: 'bottom',
  speed: 500,
  autoplayHoverPause: true,
  autoplayButtonOutput: false,
  responsive: {
    0: {
      items: 1
    },
    500: {
      items: 2,
      gutter: 18
    },
    768: {
      items: 3,
      gutter: 20
    },
    1100: {
      items: 4,
      gutter: 30
    }
  }
}

function filterProductFields(product) {
  return fieldList.filter(field => {
    if (!field in product)
      return false
    if (field === 'country' || field === 'developer_country')
      return product[field].enabled
    return product[field]
  })
};

function prettify(field, value) {
  if (field === 'manufacturer')
    return value.name
  if (field === 'country' || field === 'developer_country')
    return value.enabled ? value.name : ""
  if (field === 'complect')
    return <div dangerouslySetInnerHTML={{ __html: value }} />
  if (typeof value === 'string')
    return value.trim()
  return value
}

function rebootstrap(value) {
  if (typeof value !== 'string')
    return value
  value = value.replaceAll('col-md-4', 'col-md-2')
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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function renderTemplate(template, product) {
  // const compileFn = gana(template)
  // return compileFn({ product })
  // TODO: find solution for templates
  return template
};

export default function Product({ code }) {
  const [tnsModule, setTnsModule] = useState(null)
  const [productFields, setProductFields] = useState([])
  const [fieldNames, setFieldNames] = useState({})
  const [currentImage, setCurrentImage] = useState()
  const [galleryOpen, setGalleryOpen] = useState(false)

  const router = useRouter()

  const { status } = useSession()
  const { favorites, favoritize, unfavoritize } = useFavorites()
  const { comparisons, compare } = useComparison()

  const { data: fields } = useQuery({
    queryKey: productKeys.fields(),
    queryFn: () => getProductFields()
  })

  const { data: product, isSuccess, isLoading } = useQuery({
    queryKey: productKeys.detail(code),
    queryFn: () => loadProductByCode(code),
    enabled: code !== undefined
  })

  useEffect(() => {
    import('tiny-slider').then((module) => {
      setTnsModule(module)
    })
  }, [])

  useEffect(() => {
    if (isSuccess) {
      setProductFields(filterProductFields(product))
      if (product.image)
        setCurrentImage(product.image)
      const impressions = [
        ...product.accessories?.map((product, index) => ({
          id: product.id,
          name: product.title,
          price: product.price,
          list: 'Сопутствующие товары',
          position: index + 1
        })) ?? [],
        ...product.similar?.map((product, index) => ({
          id: product.id,
          name: product.title,
          price: product.price,
          list: 'Похожие товары',
          position: index + 1
        })) ?? []
      ]
      eCommerce({
        impressions,
        detail: {
          products: [
            {
              id: `${product.id}`,
              name: `${product.partnumber ? product.partnumber + ' ' : ''}${product.title}`,
              category: `${product.categories[0]?.name}`,
              brand: `${product.manufacturer.code}`,
              price: `${product.cost}`
            }
          ]
        }
      })
    }
  }, [product, isSuccess])

  useEffect(() => {
    if (fields !== undefined) {
      const names = {}
      Object.keys(fields).forEach((key) => {
        const name = fields[key].split(',')
        if (name.length === 1)
          name.push('')
        names[key] = name
      })
      setFieldNames(names)
    }
  }, [fields])

  useEffect(() => {
    if (isSuccess && (product.accessories || product.similar) && tnsModule !== null) {
      const carousels = []
      const carouselEls = [].slice.call(document.querySelectorAll('.tns-carousel .tns-carousel-inner'))
      carouselEls.map((carouselEl) => {
        const carousel = tnsModule.tns({ container: carouselEl, ...sliderSettings })
        // carousel.events.on('transitionEnd', carousel.updateSliderHeight);
        carousels.push(carousel)
      })
      return () => {
        carousels.map((carousel) => carousel.destroy())
      }
    }
  }, [product, isSuccess, tnsModule])

  const { ref: reviewsRef, inView: reviewsVisible } = useInView({
    rootMargin: '300px',
    triggerOnce: true,
  })

  const handleFavoritesClick = () => {
    if (status === 'authenticated') {
      if (favorites.includes(product.id))
        unfavoritize(product.id)
      else
        favoritize(product.id)
    } // TODO: else show dialog or tooltip
  }

  const handleComparisonClick = () => {
    if (comparisons.includes(product.id))
      router.push({
        pathname: '/compare',
        query: { kind: product.kind[0] }
      })
    else
      compare(product.id)
  }

  if (isLoading || !isSuccess)
    return <PageLoading className="bg-light shadow-lg rounded-3 px-4 py-3 mb-5" />

  return (
    <>
      <div className="container">
        <div className="bg-light shadow-lg rounded-3 px-4 py-3 mb-5">
          <div className="px-lg-3">
            <div className="row">
              <div className="col-lg-7 pe-lg-0">
                {currentImage ? (
                  <div className="d-block text-center">
                    <div className="position-relative w-100" style={{ aspectRatio: "4/3" }}>
                      <Image
                        src={currentImage}
                        priority
                        loading="eager"
                        fill
                        style={{ objectFit: 'contain' }}
                        alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`}
                        onClick={() => setGalleryOpen(true)}
                        itemProp="image"
                        role="button" />
                    </div>
                    {product.images && (
                      <ImageCarousel images={product.images} setImage={setCurrentImage} className="my-2" />
                    )}
                    <ImageGallery
                      currentImage={currentImage}
                      images={[
                        product.big_image || product.image,
                        ...(product.images ?? []).map(image => image.src)
                      ]}
                      open={galleryOpen}
                      setOpen={setGalleryOpen} />
                  </div>
                ) : (
                  <div className="d-none d-lg-block">
                    <NoImage size={300} block />
                  </div>
                )}
              </div>
              <div className="col-lg-5 pt-4 pt-lg-0">
                <div className="product-details ms-auto pb-3">
                  {product.enabled && product.cost > 0 && (
                    <div className="d-flex flex-row xalign-items-baseline mb-3">
                      <div className="h3 fw-normal text-accent flex-shrink-1">
                        <ProductPrice product={product} delFs="lg" itemProp="price" />
                        <span itemProp="priceCurrency" className="d-none">RUB</span>
                      </div>
                      <div className="ms-3 text-end w-100">
                        {product.discount > 0 && (
                          <OverlayTrigger
                            placement="bottom"
                            overlay={
                              <Tooltip>
                                Базовая цена в магазинах &laquo;Швейный Мир&raquo;
                                без учета скидок <b>{product.price.toLocaleString('ru')}</b>&nbsp;руб.
                                Скидка при покупке в интернет-магазине составляет{' '}
                                <b>{product.discount.toLocaleString('ru')}</b>&nbsp;руб.
                              </Tooltip>
                            }
                          >
                            <span className="badge bg-primary badge-shadow ms-2 mb-2">Скидка</span>
                          </OverlayTrigger>
                        )}
                        {product.ishot && (
                          <span className="badge bg-accent badge-shadow ms-2 mb-2">Акция</span>
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
                          {product.utilisation && (
                            <div className="mb-2">
                              { /* TODO: refactor - move to actions */}
                              <i className="ci-gift text-danger pe-2" />
                              Участник акции <Link href="/actions/utilisation/">&laquo;Утилизация&raquo;</Link>!
                              Скидка по акции <span className="price">{product.maxdiscount}%</span>!
                            </div>
                          )}
                        </div>
                      </div>
                      {product.cost > 0 ? (
                        <div className="d-flex justify-content-between align-items-center pt-2 pb-4" itemProp="offers" itemScope itemType="http://schema.org/Offer">
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
                  {(product.enabled || product.kind) && (
                    <div className="d-flex mb-4">
                      {(status === 'authenticated' && product.enabled) && (
                        <button
                          type="button"
                          onClick={handleFavoritesClick}
                          className={"btn btn-" + (favorites.includes(product.id) ? "accent" : "secondary") + " d-block w-100"}>
                          <i className="ci-heart fs-lg me-2" />
                          <span>
                            {favorites.includes(product.id) ? "В избранном" : "Отложить"}
                          </span>
                        </button>
                      )}
                      {product.kind && (
                        <button
                          type="button"
                          onClick={handleComparisonClick}
                          className={"btn btn-" + (comparisons.includes(product.id) ? "accent" : "secondary") + " d-block w-100" + (status === 'authenticated' ? " ms-3" : "")}>
                          <i className="ci-compare fs-lg me-2" />
                          <span>
                            {comparisons.includes(product.id) ? "Сравнение" : "Сравнить"}
                          </span>
                        </button>
                      )}
                    </div>
                  )}

                  {product.enabled && product.cost > 0 && (
                    <Collapsible.Root className={"mb-4" + (product.enabled ? "" : " mt-5")}>
                      <Collapsible.Trigger className="btn btn-outline-secondary btn-sm w-100">
                        <i className="ci-location text-muted lead align-middle mt-n1 me-2" />Наличие в магазинах
                      </Collapsible.Trigger>
                      <Collapsible.Panel className="card mt-1">
                        <div className="card-body">
                          <Suspense fallback={<Loading className="text-center" />}>
                            <ProductStock id={product.id} />
                          </Suspense>
                        </div>
                      </Collapsible.Panel>
                    </Collapsible.Root>
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
          <div className="pb-3 mb-md-3" itemProp="description" dangerouslySetInnerHTML={{ __html: rebootstrap(product.descr) }} />
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
                      <Link className="text-muted" href={{ pathname: '/products/[code]', query: { code: item.code } }}>
                        {item.title}
                      </Link>
                      {item.quantity > 1 && (
                        <>({item.quantity} шт.)</>
                      )}
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
          <div className="pb-3 mb-md-3" dangerouslySetInnerHTML={{ __html: rebootstrap(product.spec) }} />
        )}

        {Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
          <div className="pt-lg-2 pb-3 mb-md-3">
            <h2 className="h3 pb-2">Характеристики {product.title}</h2>
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
                        {prettify(field, product[field])}
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
              <h2 className="h3 text-center pb-4">Популярные аксессуары для {product.title}</h2>
              <div className="tns-carousel tns-controls-static tns-controls-outside">
                <div className="tns-carousel-inner">
                  {product.accessories.map((accessory) => (
                    <ProductMiniCard product={accessory} key={accessory.id} />
                  ))}
                </div>
              </div>
            </div>
          )}
          {product.similar && (
            <div className="container pt-lg-2 pb-5 mb-md-3">
              <h2 className="h3 text-center pb-4">Товары похожие на {product.title}</h2>
              <div className="tns-carousel tns-controls-static tns-controls-outside">
                <div className="tns-carousel-inner">
                  {product.similar.map((similar) => (
                    <ProductMiniCard product={similar} key={similar.id} />
                  ))}
                </div>
              </div>
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

      {product.allow_reviews && (
        <div className="border-top my-lg-3 py-5">
          <div className="container pt-md-2" id="reviews" ref={reviewsRef}>
            {reviewsVisible && (
              <Suspense fallback={<Loading className="text-center" />}>
                <ProductReviews product={product} />
              </Suspense>
            )}
          </div>
        </div>
      )}
    </>
  )
}

Product.getLayout = function getLayout(page) {
  const breadcrumbs = page.props.breadcrumbs?.map((breadcrumb) => (
    {
      href: `/catalog/${breadcrumb.path.join('/')}`,
      label: breadcrumb.label
    }
  )) ?? []

  const secondaryTitle = page.props.manufacturerLogo ? (
    <div>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img alt={page.props.manufacturer} src={page.props.manufacturerLogo} style={{ height: "60px" }} />
    </div>
  ) : null

  return (
    <PageLayout
      title={page.props.title}
      titleAddon={
        <>
          {(page.props.runame || page.props.whatis) && (
            <span className="text-white opacity-70">
              {page.props.whatis} {page.props.runame}
            </span>
          )}
          {page.props.allowReviews && <ProductRating product={page.props.id} anchor="reviews" />}
        </>
      }
      secondaryTitle={secondaryTitle}
      breadcrumbs={breadcrumbs}
      dark overlapped>
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context) {
  const code = context.params.code

  const queryClient = new QueryClient()
  const fieldsQuery = queryClient.fetchQuery({
    queryKey: productKeys.fields(),
    queryFn: () => getProductFields()
  })
  const dataQuery = queryClient.fetchQuery({
    queryKey: productKeys.detail(code),
    queryFn: () => loadProductByCode(code)
  })
  try {
    // run queries in parallel
    await fieldsQuery
    const data = await dataQuery

    const breadcrumbs = data.categories
      .filter(category => !['New', 'promo', 'Discount'].includes(category.slug))[0]?.path.breadcrumbs
      .reduce((breadcrumbs, breadcrumb) => {
        const parentPath = breadcrumbs.length > 0 ? breadcrumbs.at(-1).path : []
        breadcrumbs.push({
          label: breadcrumb.name,
          path: [...parentPath, breadcrumb.slug]
        })
        return breadcrumbs
      }, []) ?? []

    return {
      props: {
        code,
        dehydratedState: dehydrate(queryClient),
        title: data.title,
        whatis: data.whatis || null,
        runame: data.runame || null,
        manufacturer: data.manufacturer?.name || null,
        manufacturerLogo: data.manufacturer?.logo || null,
        id: data.id,
        allowReviews: data.allow_reviews,
        breadcrumbs
      },
      revalidate: 60 * 60 // <--- ISR cache: once an hour
    }
  } catch (error) {
    if (error.response?.status === 404)
      return { notFound: true }
    else
      throw (error)
  }
}

export async function getStaticPaths() {
  const filters = [
    recomendedFilters,
    firstPageFilters
  ]
  const included = new Set()
  const paths = []
  for (let filter of filters) {
    let page = 1
    while (page !== undefined) {
      const products = await loadProducts(page, 100, filter, null)
      paths.push(...products.results.filter((product) => !included.has(product.id)).map((product) => {
        included.add(product.id)
        return {
          params: {
            code: product.code
          }
        }
      }))
      if (products.totalPages > products.currentPage)
        page += 1
      else
        page = undefined
    }
  }
  return { paths, fallback: true }
}
