import Layout from '@/components/layout';

export default function Index() {
    return (
        <div className="text-center">
            <img src="/i/jumbo.jpg" className="img-fluid" alt="Нитки Дор Так" />
        </div>
    )
}

Index.getLayout = function getLayout(page) {
    return (
        <Layout hideTitle>
            {page}
        </Layout>
    )
}
