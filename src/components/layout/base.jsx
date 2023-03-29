import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

import TopBar from './topbar';
import BottomBar from './bottombar';
import HandheldBottomBar from './handheld-bottombar';

export default function BaseLayout({ title, htmlTitle, hideSignIn, hideCartNotice, contentWrapper, children, ...props }) {
    const [topMenuOpen, setTopMenuOpen] = useState(false);

    const router = useRouter();

    useEffect(() => {
        const handleRouteChange = () => {
            setTopMenuOpen(false);
        };
        router.events.on('routeChangeStart', handleRouteChange);
        return () => {
            router.events.off('routeChangeStart', handleRouteChange)
        }
    }, [router.events, setTopMenuOpen]);

    return (
        <>
            <Head>
                <title>{`${(htmlTitle || title) ? (htmlTitle || title) + " - " : ""}Швейный Мир`}</title>
                <meta name="description" content="Швейный Мир - швейные, вышивальные и вязальные машины, оверлоки и аксессуары" />
                <meta name="keywords" content="швейные машины, вышивальные и вязальные машины, оверлоки и аксессуары во всероссийской сети супермаркетов Швейный Мир, швейная, швейные, вышивальная, вышивальные, вязальная, вязальные, машинка, машина, машинки, машины, оверлок, оверлоки,  шитье, вышивка, вязание, купить, интернет, магазин, pfaff, brother, janome, bernina, husqvarna, huskystar, viking, оверлок, строчка, петля, челнок, стежок, ткань, рукав" />
            </Head>
            <div className="d-flex flex-column min-vh-100">
                <main className="page-wrapper">
                    <TopBar hideSignIn={hideSignIn} hideCartNotice={hideCartNotice} topMenuOpen={topMenuOpen} toggleTopMenu={() => setTopMenuOpen((open) => !open)} />
                    {contentWrapper({title, children, ...props})}
                </main>

                <BottomBar />
            </div>
            <HandheldBottomBar topMenuOpen={topMenuOpen} toggleTopMenu={() => setTopMenuOpen((open) => !open)} />

            { /* Back To Top Button */ }
            <a className="btn-scroll-top" href="#top" data-scroll>
                <span className="btn-scroll-top-tooltip text-muted fs-sm me-2">Начало</span>
                <i className="btn-scroll-top-icon ci-arrow-up">   </i>
            </a>
        </>
    )
}

BaseLayout.defaultProps = {
    hideSignIn: false,
    hideCartNotice: false,
    contentWrapper: ({children}) => children
};
