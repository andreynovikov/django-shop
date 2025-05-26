import Head from 'next/head';

import Header from '@/components/layout/header';
import Footer from '@/components/layout/footer';
import PageTitle from '@/components/layout/page-title';

import { useSite } from '@/lib/site';

export default function Layout({ title, hideTitle, contentWrapper, children, ...props }) {
    const { site } = useSite();

    return (
        <>
            <Head>
                <title>{`${ title ? title : "Дор Так - Швейные нитки оптом и в розницу"}`}</title>
                <meta charSet="utf-8" />
                <meta name="description" content={site.description || ""} />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <meta name="robots" content="all,follow" />
                <meta name="yandex-verification" content="9067b839ade4914a" />
                <meta name="yandex-verification" content="ffa29a305777f97e" />
                <link rel="icon" href="/images/favicon.png" type="image/png" />
            </Head>

            <Header />
            <main className="container my-4">
                {!hideTitle && <PageTitle title={title} /> }
                {contentWrapper({title, children, ...props})}
            </main>
            <Footer />
        </>
    )
}

Layout.defaultProps = {
    hideTitle: false,
    contentWrapper: ({children}) => children
};
