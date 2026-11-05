'use client'

import Link from 'next/link'

import { Menu } from '@base-ui/react/menu'

const categories = [
  [
    { href: '/catalog/electronic/', image: '/i/newsingerco/productsElectronic.jpg', alt: 'Электронные швейные машины', label: 'Электронные машины' },
    { href: '/catalog/basic/', image: '/i/newsingerco/productsMechanical.jpg', alt: 'Механические швейные машины', label: 'Механические машины' },
    { href: '/catalog/serger/', image: '/i/newsingerco/productsSerger.jpg', alt: 'Оверлоки', label: 'Оверлоки' },
    { href: '/catalog/irons/', image: '/i/newsingerco/productsGarment.jpg', alt: 'Уход за одеждой и домом', label: 'Уход за одеждой и домом' },
  ],
  [
    { href: '/catalog/Feet/', image: '/i/newsingerco/productsFeet.jpg', alt: 'Лапки для швейных машин', label: 'Лапки' },
    { href: '/catalog/Accessories/', image: '/i/newsingerco/productsNotions.jpg', alt: 'Аксессуары', label: 'Аксессуары' },
  ],
]

// The "ПРОДУКЦИЯ" mega menu of the header navigation
export default function ProductsMenu() {
  return (
    <div>
      <Menu.Root>
        <Menu.Trigger className="navLink dropdown-toggle" nativeButton={false} render={<a />}>
          ПРОДУКЦИЯ
        </Menu.Trigger>
        <Menu.Portal>
          <Menu.Positioner sideOffset={8} align="start">
            <Menu.Popup className="dropdown-menu show position-static si-mega-menu rounded-0 shadow border-0">
              <div className="container-fluid p-3">
                {categories.map((row, index) => (
                  <div className="row" key={index}>
                    {row.map((category) => (
                      <div className="col-md-3 fw-bold text-center mb-3" key={category.href}>
                        <Menu.LinkItem className="dropdown-item" render={<Link href={category.href} />} closeOnClick>
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={category.image} alt={category.alt} width="147" height="102" />
                          <div>{category.label}</div>
                        </Menu.LinkItem>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </Menu.Popup>
          </Menu.Positioner>
        </Menu.Portal>
      </Menu.Root>
    </div>
  )
}
