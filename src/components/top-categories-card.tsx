/* eslint-disable @next/next/no-img-element */
import Link from 'next/link'

export default function TopCategoriesCard() {
  return (
    <div className="relative mx-1 flex min-w-0 flex-col rounded-lg bg-white shadow-lg md:mx-12 xl:mx-0">
      <div className="px-4 pt-5 pb-0">
        <div className="flex flex-wrap justify-around">
          <div className="mb-7.5 w-1/2 text-center md:w-1/3 lg:w-auto lg:px-2">
            <Link href="/catalog/sewing_machines/">
              <img src="/i/categories/compsewing.svg" alt="Швейные машины" height="75" width="75" className="inline" />
              <div>Швейные<br />машины</div>
            </Link>
          </div>
          <div className="mb-7.5 w-1/2 text-center md:w-1/3 lg:w-auto lg:px-2">
            <Link href="/catalog/embroidery_machines/">
              <img src="/i/categories/embroidery.svg" alt="Швейно-вышивальные машины" height="75" width="94" className="inline" />
              <div>Вышивальные<br />машины</div>
            </Link>
          </div>
          <div className="mb-7.5 w-1/2 text-center md:w-1/3 lg:w-auto lg:px-2">
            <Link href="/catalog/sergers/">
              <img src="/i/categories/overlock.svg" alt="Оверлоки, коверлоки и распошивальные машины" height="75" width="75" className="inline" />
              <div>Оверлоки и<br />коверлоки</div>
            </Link>
          </div>
          <div className="mb-7.5 w-1/2 text-center md:w-1/3 lg:w-auto lg:px-2">
            <Link href="/catalog/knitting_machines/">
              <img src="/i/categories/knitting.svg" alt="Вязальные машины" height="75" width="94" className="inline" />
              <div>Вязальные<br />машины</div>
            </Link>
          </div>
          <div className="mb-7.5 w-1/2 text-center md:w-1/3 lg:w-auto lg:px-2">
            <Link href="/catalog/accessories/threads/">
              <img src="/i/categories/threads.svg" alt="Нитки" height="75" width="75" className="inline" />
              <div>Нитки</div>
            </Link>
          </div>
          <div className="mb-7.5 w-1/2 text-center md:w-1/3 lg:w-auto lg:px-2">
            <Link href="/catalog/accessories/">
              <img src="/i/categories/accessories.svg" alt="Аксессуары" height="75" width="75" className="inline" />
              <div>Аксессуары</div>
            </Link>
          </div>
          <div className="mb-7.5 hidden text-center lg:block lg:px-2">
            <Link href="/catalog/parts/">
              <img src="/i/categories/parts.svg" alt="Запасные части" height="75" width="75" className="inline" />
              <div>Запасные<br />части</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
