import { useRouter } from 'next/router';
import Link from 'next/link';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import Layout from '@/components/layout';
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

    if (router.isFallback || !isSuccess) {
        return (
            <div className="container d-flex align-items-center justify-content-center text-secondary mb-6">
                <div className="spinner-border mx-3" role="status" aria-hidden="true"></div>
                <strong>Загружается...</strong>
            </div>
        )
    }

    if (isSuccess)
        return (
            <>
                { category.children && (
                    <ul className="catalog">
                        { /* TODO: filter hidden (here or in API) */ }
                        {category.children.map((subcategory) => (
                            <li className="category" key={subcategory.id}>
                                <Link href={`/catalog/${category.path.uri}/${subcategory.slug}`}>
                                    { subcategory.name }
                                </Link>
                            </li>
                        ))}
                    </ul>
                )}
                <div className="product-list py-2">
                    { isProductsSuccess && products.results.map((product) => (
                        <ProductCard product={product} key={product.id} />
                    ))}
                </div>
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

export async function getStaticProps(context) {
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
        revalidate: 60 * 60 * 24 // <--- ISR cache: once a day
    };
}

export async function getStaticPaths() {
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

    const categories = await loadCategories();
    const {paths} = categories.reduce(getPaths, {paths: [], root: []});

    return { paths, fallback: true };
}
