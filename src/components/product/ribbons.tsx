import { ProductInfo } from '@/lib/types'

const ribbonClass = "absolute z-999 inline-block px-[15px] pt-[3px] pb-[5px] text-center text-[.8rem] tracking-[.3em] text-white uppercase before:absolute before:-bottom-3.5 before:left-0 before:border-t-14 before:border-l-12 before:border-l-transparent before:content-['']"

const variants = {
  primary: 'bg-primary before:border-t-primary-dark',
  info: 'bg-info before:border-t-info-dark',
}

// The card's ribbons hang over its left edge, the detail page's lie on the image
const positions = {
  card: ['top-2.5 -left-2.75', 'top-15 -left-2.75'],
  detail: ['top-5 left-1', 'top-20 left-1'],
}

// Labels of new and recommended products, stacked over the top left corner of the product image
export default function ProductRibbons({ product, detail = false }: {
  product: Pick<ProductInfo, 'isnew' | 'recomended'>,
  detail?: boolean
}) {
  const ribbons: { variant: keyof typeof variants, label: string }[] = []
  if (product.isnew)
    ribbons.push({ variant: 'primary', label: 'Новинка' })
  if (product.recomended)
    ribbons.push({ variant: 'info', label: 'Рекомендуем' })

  return ribbons.map(({ variant, label }, index) => (
    <div className={`${ribbonClass} ${variants[variant]} ${positions[detail ? 'detail' : 'card'][index]}`} key={variant}>
      {label}
    </div>
  ))
}
