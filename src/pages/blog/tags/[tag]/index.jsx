import { dehydrate, QueryClient } from '@tanstack/react-query';

import { blogKeys, loadBlogEntries, loadBlogTags } from '@/lib/queries';

import BlogEntries from './[page]';

export default BlogEntries;

export async function getStaticProps(context) {
    const tag = context.params.tag;
    const filters = [{ field: 'tags', value: tag }];
    const queryClient = new QueryClient();
    await queryClient.prefetchQuery({
        queryKey: blogKeys.list('1', filters),
        queryFn: () => loadBlogEntries('1', filters)
    });

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            tag,
            currentPage: '1'
        }
    };
}

export async function getStaticPaths() {
    const tags = await loadBlogTags();
    const paths = tags.map((tag) => ({
        params: { tag: tag.name }
    }));
    return { paths, fallback: 'blocking' };
}
