import { dehydrate, QueryClient, useQuery } from 'react-query';

import BaseLayout from '@/components/layout/base';
import ProductCard from '@/components/product-card';

import { productKeys, loadProducts } from '@/lib/queries';
import useCatalog from '@/lib/catalog';

const filters = [
    { field: 'gift', value: 1 },
    { field: 'show_on_sw', value: 1 }
];
const sort = '-price';

export default function Index() {
    const { data, isSuccess, isLoading, isError } = useQuery(productKeys.list(null, null, filters, sort), () => loadProducts(null, null, filters, sort));

    useCatalog();

    if (isSuccess) {
        return (
            <section className="container pt-5">
                <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
                    <h2 className="h3 mb-0 pt-3 me-2">Идеи для подарков</h2>
                </div>
                <div className="row pt-2 mx-n2">
                    {data.results.map((product) => (
                        <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                            <ProductCard product={product} />
                            <hr className="d-sm-none" />
                        </div>
                    ))}
                </div>
            </section>
        );
    }

    if (isLoading) {
        return <div className="center">Loading...</div>;
    }

    if (isError) {
        return (
            <div className="center">Error!</div>
        );
    }

    return <></>;
}

Index.getLayout = function getLayout(page) {
    return (
        <BaseLayout>
            {page}
        </BaseLayout>
    )
}

export async function getStaticProps(context) {
    // const id = context.params?.id;
    const queryClient = new QueryClient();

    await queryClient.prefetchQuery(productKeys.list(null, null, filters, sort), () => loadProducts(null, null, filters, sort));

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
