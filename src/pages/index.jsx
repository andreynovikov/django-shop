import Layout from '@/components/layout';

export default function Index() {
    return (
        null
    )
}

Index.getLayout = function getLayout(page) {
    return (
        <Layout>
            {page}
        </Layout>
    )
}

