import { dehydrate, QueryClient } from 'react-query';

import { blogKeys, loadBlogEntries, loadBlogCategories, loadBlogCategory } from '@/lib/queries';

import BlogEntries from './[page]';

export default BlogEntries;

export async function getStaticProps(context) {
    const slug = context.params.slug;
    const queryClient = new QueryClient();
    const category = await queryClient.fetchQuery(blogKeys.category(slug), () => loadBlogCategory(slug));
    const filters = [{ field: 'categories', value: category.id }];
    await queryClient.prefetchQuery(blogKeys.list('1', filters), () => loadBlogEntries('1', filters));

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            category,
            currentPage: '1'
        }
    };
}

export async function getStaticPaths() {
    const categories = await loadBlogCategories();
    const paths = categories.map((category) => ({
        params: { slug: category.slug }
    }));
    return { paths, fallback: 'blocking' };
}
