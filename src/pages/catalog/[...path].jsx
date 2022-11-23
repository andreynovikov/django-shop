import { useRouter } from 'next/router';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import Layout from '@/components/layout';
import PageTitle from '@/components/layout/page-title';
import ProductCard from '@/components/product/card';

import { categoryKeys, productKeys, loadCategories, loadCategory, loadProducts } from '@/lib/queries';

const baseFilters = [
    { field: 'enabled', value: 1}
];
const defaultOrder = 'title';

export default function Category({path, filters, order}) {
    const router = useRouter();

    const { data: category, isSuccess } = useQuery(
        categoryKeys.detail(path),
        () => loadCategory(path),
        {
            enabled: !!path // path is not set on first render
        }
    );

    const { data: products, isSuccess: isProductsSuccess } = useQuery(
        productKeys.list(1, 1000, filters, order),
        () => loadProducts(1, 1000, filters, order),
        {
            enabled: !!filters && !!order
        }
    );

    if (router.isFallback) {
        // TODO: Test and make user friendly
        return <div>Loading...</div>
    }

    if (isSuccess)
        return (
            <>
                <PageTitle title={category.name} description={category.description} />
	            <main>
                    <div className="container mb-5">
		                <div className="row">
		                    <div className="products-grid col-12 sidebar-none">
		                        <div className="row">
                                    {isProductsSuccess && products.results.map((product) => (
                                        <div className="col-lg-4 col-sm-6" key={product.id}>
                                            <ProductCard product={product} />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </>
        )

    return null
}

Category.getLayout = function getLayout(page) {
    return (
        <Layout title={page.props.title}>
            {page}
        </Layout>
    )
}

export async function getServerSideProps(context) {
    const path = context.params?.path;
    const queryClient = new QueryClient();
    const category = await queryClient.fetchQuery(categoryKeys.detail(path), () => loadCategory(path));
    const productFilters = [{field: 'categories', value: category.id}, ...baseFilters];
    const productOrder = category.product_order || defaultOrder;

    await queryClient.prefetchQuery(
        productKeys.list(1, 1000, productFilters, productOrder),
        () => loadProducts(1, 1000, productFilters, productOrder)
    );

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            title: category.name,
            filters: productFilters,
            order: productOrder,
            path,
        },
        //revalidate: 60 * 60 * 24 // <--- ISR cache: once a day
    };
}

export async function xgetStaticPaths() {
    console.log("getStaticPaths");
    const getPaths = ({paths, root}, category) => {
        const path = root.concat([category.slug]);
        paths.push({
            params: {path},
        });
        if (category.children) {
            const {paths: rpaths} = category.children.reduce(getPaths, {paths, root: path});
            return {paths: rpaths, root};
        }
        return {paths, root};
    };

    //const categories = await loadCategories();
    //const {paths} = categories.reduce(getPaths, {paths: [], root: []});

    return { paths: [], fallback: true }
    //return { paths, fallback: true };
}
