import Link from "next/link"
import { IconChevronRight, IconHome } from '@tabler/icons-react'

export type Breadcrumb = {
  label: string,
  href?: string
}

export default function Breadcrumbs({
  items,
  dark
}: {
  items: Breadcrumb[],
  dark: boolean
}) {
  if (items.length === 0)
    return null

  const linkClass = `transition-colors ${dark ? 'text-white hover:text-white' : 'text-gray-700 hover:text-primary'}`
  const divider = <IconChevronRight size={12} stroke={1.5} aria-hidden className={`mx-2 ${dark ? 'text-white/50' : 'text-[#a8aeb9]'}`} />

  return (
    <nav aria-label="breadcrumb">
      <ol className="mb-2 flex flex-wrap items-center justify-center text-ms lg:justify-start">
        <li>
          <Link className={linkClass} href="/" aria-label="Главная"><IconHome size={14} stroke={1.5} className="-mt-0.5 align-middle" /></Link>
        </li>
        {items.map((item, index) => (
          <li key={item.label}
            className={`flex items-center ${index === items.length - 1 ? `cursor-default ${dark ? 'text-white/60' : 'text-muted'}` : ''}`}
            aria-current={index === items.length - 1 ? 'page' : undefined}>
            {divider}
            {item.href ? (
              <Link className={linkClass} href={item.href}>{item.label}</Link>
            ) : (
              item.label
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
