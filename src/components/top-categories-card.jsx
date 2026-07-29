/* eslint-disable @next/next/no-img-element */
import Link from 'next/link'

export default function TopCategoriesCard() {
  return (
    <div className="card mx-1 mx-md-5 mx-xl-0 border-0 shadow-lg">
      <div className="card-body px-3 pb-0">
        <div className="row g-0 g-lg-3 justify-content-center">
          <div className="d-none d-lg-flex col-6 col-md-4 col-lg-auto mb-grid-gutter text-center flex-grow-1" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <div className="bg-white"></div>
            <div className="nav-link px-0"></div>
          </div>
          <div className="col-6 col-md-4 col-lg-auto mb-grid-gutter text-center" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <Link href="/catalog/sewing_machines/">
              <div style={{ background: 'white' }}><img src="/i/categories/sewing.svg" alt="Механические швейные машины" /></div>
              <div className="nav-link px-0">Механические<br />швейные машины</div>
            </Link>
          </div>
          <div className="col-6 col-md-4 col-lg-auto mb-grid-gutter text-center" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <Link href="/catalog/comp_sewing_machines/">
              <div className="bg-white"><img src="/i/categories/compsewing.svg" alt="Электронные швейные машины" /></div>
              <div className="nav-link px-0">Электронные<br />швейные машины</div>
            </Link>
          </div>
          <div className="col-6 col-md-4 col-lg-auto mb-grid-gutter text-center" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <Link href="/catalog/sewing_embroidery_machines/">
              <div className="bg-white"><img src="/i/categories/embroidery.svg" alt="Швейно-вышивальные машины" /></div>
              <div className="nav-link px-0">Машины<br />с&nbsp;вышивкой</div>
            </Link>
          </div>
          <div className="col-6 col-md-4 col-lg-auto mb-grid-gutter text-center" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <Link href="/catalog/overlock/">
              <div className="bg-white"><img src="/i/categories/overlock.svg" alt="Оверлоки и коверлоки" /></div>
              <div className="nav-link px-0">Оверлоки</div>
            </Link>
          </div>
          <div className="col-6 col-md-4 col-lg-auto mb-grid-gutter text-center" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <Link href="/catalog/coverpro/">
              <div className="bg-white"><img src="/i/categories/prom.svg" alt="Плоскошовные машины" /></div>
              <div className="nav-link px-0">Плоскошовные<br />машины</div>
            </Link>
          </div>
          <div className="col-6 col-md-4 col-lg-auto mb-grid-gutter text-center" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <Link href="/catalog/accessories/">
              <div className="bg-white"><img src="/i/categories/accessories.svg" alt="Аксессуары" /></div>
              <div className="nav-link px-0">Аксессуары</div>
            </Link>
          </div>
          <div className="d-none d-lg-flex col-6 col-md-4 col-lg-auto mb-grid-gutter text-center flex-grow-1" style={{ backgroundImage: "url('/i/categories/gifts.svg')", backgroundRepeat: 'no-repeat', }}>
            <div className="bg-white"></div>
            <div className="nav-link px-0"></div>
          </div>

        </div>
      </div>
    </div>
  )
}
