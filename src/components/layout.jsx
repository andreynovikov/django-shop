import Head from 'next/head';
import Link from 'next/link';

import Header from '@/components/layout/header';
import Footer from '@/components/layout/footer';
import SvgIcon from '@/components/svg-icon';

export default function BaseLayout({ title, contentWrapper, children, ...props }) {
    return (
        <>
            <Head>
                <title>{`${ title ? title + " - " : ""}Family`}</title>
                <meta charset="utf-8" />
                <meta name="description" content="Швейные машины и аксессуары Family" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <meta name="robots" content="all,follow" />
	            <meta name="yandex-verification" content="6e328a4eff438f46" />
	            <meta name="yandex-verification" content="f8bbdebb7f2a6f33" />
	            <meta name="yandex-verification" content="9d6d54901642b029" />
	            <meta name="yandex-verification" content="0c2c065329da0681" />
	            <meta name="yandex-verification" content="6462f73cb6863828" />
	            <meta name="google-site-verification" content="EDYJTRf3vq0dN_qGl4AKqLJ3QzazyENONErE2gIyHzo" />
            </Head>

            <Header />
            <main>
                {contentWrapper({title, children, ...props})}
            </main>
            <Footer />
        </>
    )
}

BaseLayout.defaultProps = {
    contentWrapper: ({children}) => children
};
