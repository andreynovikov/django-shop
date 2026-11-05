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
        <Menu.Trigger
          className="navLink after:ms-1 after:inline-block after:border-x-[0.3em] after:border-t-[0.3em] after:border-b-0 after:border-x-transparent after:border-t-current after:align-[0.255em]"
          nativeButton={false}
          render={<a />}>
          ПРОДУКЦИЯ
        </Menu.Trigger>
        <Menu.Portal>
          <Menu.Positioner sideOffset={8} align="start">
            <Menu.Popup className="w-screen max-w-[960px] bg-white px-4 py-6 text-left shadow-lg">
              {categories.map((row, index) => (
                <div className="grid gap-x-6 md:grid-cols-4" key={index}>
                  {row.map((category) => (
                    <div className="mb-4 text-center font-bold" key={category.href}>
                      <Menu.LinkItem className="block text-primary outline-none hover:no-underline" render={<Link href={category.href} />} closeOnClick>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img className="mx-auto" src={category.image} alt={category.alt} width="147" height="102" />
                        <div>{category.label}</div>
                      </Menu.LinkItem>
                    </div>
                  ))}
                </div>
              ))}
            </Menu.Popup>
          </Menu.Positioner>
        </Menu.Portal>
      </Menu.Root>
    </div>
  )
}
