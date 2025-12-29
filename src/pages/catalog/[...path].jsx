import { useRouter } from 'next/router';
import Link from 'next/link';
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query';

import Layout from '@/components/layout';
import ProductCard from '@/components/product/card';

import { categoryKeys, productKeys, loadCategories, loadCategory, loadProducts } from '@/lib/queries';

const baseFilters = [
    { field: 'enabled', value: 1}
];
const defaultOrder = 'title';

export default function Category({path, filters, order}) {
    const router = useRouter();

    const { data: category, isSuccess } = useQuery({
        queryKey: categoryKeys.detail(path),
        queryFn: () => loadCategory(path),
        enabled: !!path // path is not set on first render
    });

    const { data: products, isSuccess: isProductsSuccess } = useQuery({
        queryKey: productKeys.list(1, 1000, filters, order),
        queryFn: () => loadProducts(1, 1000, filters, order),
        enabled: !!filters && !!order
    });

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
            <div className="d-flex flex-wrap justify-content-between py-2" style={{gap: "20px"}}>
                { category.promo_image && (
                    <div>
                        <img src={ category.promo_image } className="si-category-image" width={ category.promo_image_width } height={ category.promo_image_height } alt="" />
                    </div>
                )}
                { category.children && (
                    <ul className="si-category-list fs-md order-sm-first">
                        { /* TODO: filter hidden (here or in API) */ }
                        {category.children.map((subcategory) => (
                            <li key={subcategory.id}>
                                <Link href={`/catalog/${category.path.uri}/${subcategory.slug}`}>
                                    { subcategory.name }
                                </Link>
                            </li>
                        ))}
                    </ul>
                )}
                { isProductsSuccess && products.results.map((product) => (
                    <ProductCard product={product} key={product.id} />
                ))}
            </div>
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
    const category = await queryClient.fetchQuery({
        queryKey: categoryKeys.detail(path),
        queryFn: () => loadCategory(path)
    });
    const productFilters = [{field: 'categories', value: category.id}, ...baseFilters];
    const productOrder = category.product_order || defaultOrder;

    await queryClient.prefetchQuery({
        queryKey: productKeys.list(1, 1000, productFilters, productOrder),
        queryFn: () => loadProducts(1, 1000, productFilters, productOrder)
    });

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
