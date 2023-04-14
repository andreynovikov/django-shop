import { dehydrate, QueryClient, useQuery } from 'react-query';

import PageLayout from '@/components/layout/page';
import BlogEntryPreview from '@/components/blog/entry-preview';
import PageSelector from '@/components/page-selector';

import { blogKeys, loadBlogEntries } from '@/lib/queries';

import range from 'lodash/range';

export default function BlogEntries({currentPage}) {

    const { data: entries, isSuccess } = useQuery(
        blogKeys.list(currentPage, null),
        () => loadBlogEntries(currentPage, null)
    );

    if (isSuccess)
        return (
            <div className="container pb-5 mb-2 mb-md-4">
                { /* TODO: add featured posts carousel */ }
                <hr className="mt-5" />
                <div className="row justify-content-center pt-5 mt-2">
                    <section className="col-lg-9">
                        {entries.results.map((entry, index) => (
                            < BlogEntryPreview entry={entry} last={index === entries.results.length - 1} key={entry.id} />
                        ))}

                        { entries.totalPages > 1 && (
                            <>
                                <hr className="my-3" />
                                <PageSelector
                                    pathname="/blog/entries/[page]"
                                    path={[]}
                                    totalPages={entries.totalPages}
                                    currentPage={entries.currentPage} />
                            </>
                        )}
                    </section>
                </div>
            </div>
        );

    return null;
}

BlogEntries.getLayout = function getLayout(page) {
    return (
        <PageLayout title="Блог">
            {page}
        </PageLayout>
    )
}

export async function getStaticProps(context) {
    const currentPage = context.params?.page || '1';
    if (currentPage === '1' && context.params?.page) {
        return {
            redirect: {
                destination: '/blog/entries/',
                permanent: false
            }
        }
    }

    const queryClient = new QueryClient();
    await queryClient.prefetchQuery(blogKeys.list(currentPage, null), () => loadBlogEntries(currentPage, null));

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            currentPage
        }
    };
}

export async function getStaticPaths() {
    const entries = await loadBlogEntries(null, null);
    const pages = Math.ceil(entries.count / entries.pageSize);
    const paths = range(2, pages).map((page) => ({
        params: { page: String(page) }
    }));
    return { paths, fallback: false };
}
