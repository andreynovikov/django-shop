import { dehydrate, QueryClient, useQuery } from 'react-query';

import Layout from '@/components/layout';
import PageTitle from '@/components/layout/page-title';

import { newsKeys, loadNews } from '@/lib/queries';

import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function News() {
    const { data, isSuccess } = useQuery(newsKeys.lists(), () => loadNews());

    return (
        <>
            <PageTitle title="Новости" />
            <section className="pb-5">
                <div className="container">
                    { isSuccess && data.map((article) => (
                        <div className="pb-4" key={article.id}>
                            <h2 className="mb-5 text-muted">{ article.title }</h2>
                            <div className="mb-2 text-muted">{ moment(article.publish_date).format('LL') }</div>
                            { article.image && (
                                <img className="rounded mx-auto mb-2 d-block" style={{maxHeight: "200px"}} src={article.image} alt={article.title} />
                            )}
                            <div className="text-lg" dangerouslySetInnerHTML={{__html: article.content }}></div>
                        </div>
                    ))}
                </div>
            </section>
        </>
    )
}

News.getLayout = function getLayout(page) {
    return (
        <Layout title="Новости">
            {page}
        </Layout>
    )
}

export async function getStaticProps() {
    const queryClient = new QueryClient();
    await queryClient.fetchQuery(newsKeys.lists(), () => loadNews());

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
