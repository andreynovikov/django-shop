import Link from 'next/link'

// Static, the category images are served from the site's /media/
export default function HomePage() {
  return (
    <div className="d-flex flex-wrap justify-content-between py-2" style={{ gap: "20px" }}>
      <div className="product_display text-center">
        <h3>
          <Link href="/catalog/electronic/">Электронные машины</Link>
        </h3>
        <div className="thumb">
          <Link href="/catalog/electronic/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/products/Singer/Singer9960.jpg" alt="Электронные машины" />
          </Link>
        </div>
      </div>
      <div className="product_display text-center">
        <h3>
          <Link href="/catalog/basic/">Механические машины</Link>
        </h3>
        <div className="thumb">
          <Link href="/catalog/basic/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/products/Singer/Singer_2290.jpg" alt="Механические машины" />
          </Link>
        </div>
      </div>
      <div className="product_display text-center">
        <h3>
          <Link href="/catalog/serger/">Оверлоки</Link>
        </h3>
        <div className="thumb">
          <Link href="/catalog/serger/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/products/Singer/Singer_14hd854.jpg" alt="Оверлоки" />
          </Link>
        </div>
      </div>
      <div className="product_display text-center">
        <h3>
          <Link href="/catalog/irons/">Уход за домом</Link>
        </h3>
        <div className="thumb">
          <Link href="/catalog/irons/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/products/Singer/Singer4020.jpg" alt="Уход за домом" />
          </Link>
        </div>
      </div>
      <div className="product_display text-center">
        <h3>
          <Link href="/catalog/Feet/">Лапки</Link>
        </h3>
        <div className="thumb">
          <Link href="/catalog/Feet/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/categories/featured-presser_feet_pzJu4kE.png" alt="Лапки" />
          </Link>
        </div>
      </div>
      <div className="product_display text-center">
        <h3>
          <Link href="/catalog/Accessories/">Аксессуары</Link>
        </h3>
        <div className="thumb">
          <Link href="/catalog/Accessories/">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/media/categories/featured-notions_rmKezuP.png" alt="Аксессуары" />
          </Link>
        </div>
      </div>
    </div>
  )
}
