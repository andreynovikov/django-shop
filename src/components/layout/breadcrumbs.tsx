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
    return (
        <nav aria-label="breadcrumb">
            <ol className={`breadcrumb justify-content-center justify-content-lg-end${dark ? ' breadcrumb-light' : ''}`}>
                <li className="breadcrumb-item"><a className="text-nowrap" href="index.html"><i className="ci-home"></i>Home</a></li>
                {items.map((item, index) => (
                    <li key={item.href} className={`breadcrumb-item text-nowrap${index === items.length - 1 ? ' active' : ''}`}>
                        {item.href ? (
                            <a href={item.href}>{item.label}</a>
                        ) : (
                            item.label
                        )}
                    </li>
                ))}
            </ol>
        </nav>
    )
}