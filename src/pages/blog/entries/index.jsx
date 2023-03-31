import { dehydrate, QueryClient } from 'react-query';

import { blogKeys, loadBlogEntries } from '@/lib/queries';

import BlogEntries from './[page]';

export default BlogEntries;

export async function getStaticProps() {
    const queryClient = new QueryClient();
    await queryClient.prefetchQuery(blogKeys.list('1', null), () => loadBlogEntries('1', null));

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            currentPage: '1'
        }
    };
}
