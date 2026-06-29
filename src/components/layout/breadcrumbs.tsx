import Link from "next/link"

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

  return (
    <nav aria-label="breadcrumb">
      <ol className={`breadcrumb mb-2 justify-content-center justify-content-lg-start${dark ? ' breadcrumb-light' : ''}`}>
        <li className="breadcrumb-item"><Link href="/"><i className="ci-home me-0" /></Link></li>
        {items.map((item, index) => (
          <li key={item.label} className={`breadcrumb-item${index === items.length - 1 ? ' active' : ''}`}>
            {item.href ? (
              <Link href={item.href}>{item.label}</Link>
            ) : (
              item.label
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}