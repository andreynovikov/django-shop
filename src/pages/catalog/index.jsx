import Catalog from '@/components/catalog'
import PageLayout from '@/components/layout/page'

export default function CatalogPage() {
    return (
        <div className="container py-5 mb-2 mb-md-4">
            <Catalog />
        </div>
    )
}

CatalogPage.getLayout = function getLayout(page) {
    return (
        <PageLayout title="Каталог" dark>
            {page}
        </PageLayout>
    )
}
