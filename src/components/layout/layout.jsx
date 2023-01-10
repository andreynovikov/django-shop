import Head from 'next/head';

import Header from '@/components/layout/header';
import Footer from '@/components/layout/footer';
import PageTitle from '@/components/layout/page-title';

import { useSite } from '@/lib/site';

export default function Layout({ title, hideTitle, hideTitleBorder, contentWrapper, children, ...props }) {
    const { site } = useSite();

    return (
        <>
            <Head>
                <title>{`${ title ? title + " - " : ""}${site.title ? site.title : ""}`}</title>
                <meta charSet="utf-8" />
                <meta name="description" content={site.description || ""} />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <meta name="robots" content="all,follow" />
            </Head>

            <Header />
            <main>
                {!hideTitle && <PageTitle title={title} border={!hideTitleBorder} /> }
                {contentWrapper({title, children, ...props})}
            </main>
            <Footer />
        </>
    )
}

Layout.defaultProps = {
    hideTitle: false,
    hideTitleBorder: false,
    contentWrapper: ({children}) => children
};
