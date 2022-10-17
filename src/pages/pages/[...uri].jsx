import { useRouter } from 'next/router';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import PageLayout from '@/components/layout/page';

import { withClient, pageKeys, loadPages, loadPage } from '@/lib/queries';

export default function Page() {
    const router = useRouter();
    const { uri } = router.query;

    const { data, isSuccess, isLoading, isError } = useQuery(pageKeys.detail(uri), () => withClient(loadPage, uri));

    return (
        <div className="container py-5 mb-2 mb-md-4">
            { isSuccess && <div dangerouslySetInnerHTML={{__html: data.content }}></div> }
        </div>
    )
}

Page.getLayout = function getLayout(page) {
    return (
        <PageLayout title={page.props.title}>
            {page}
        </PageLayout>
    )
}

export async function getStaticProps(context) {
    const uri = context.params?.uri;
    const queryClient = new QueryClient();
    const data = await queryClient.fetchQuery(pageKeys.detail(uri), () => withClient(loadPage, uri));

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            title: data.title
        }
    };
}

export async function getStaticPaths() {
    const pages = await withClient(loadPages);
    const paths = pages.map((page) => ({
        params: { uri: page.url.slice(1, -1).split('/') },
    }))
    return { paths, fallback: false }
}
