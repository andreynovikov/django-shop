import Head from 'next/head';

import Topbar from './topbar';

export default function BaseLayout({ title, htmlTitle, hideSignIn, hideCartNotice, contentWrapper, children, ...props }) {
    return (
        <>
            <Head>
                <title>{`${(htmlTitle || title) ? (htmlTitle || title) + " - " : ""}Швейный Мир`}</title>
                <meta name="description" content="Швейный Мир - швейные, вышивальные и вязальные машины, оверлоки и аксессуары" />
                <meta name="keywords" content="швейные машины, вышивальные и вязальные машины, оверлоки и аксессуары во всероссийской сети супермаркетов Швейный Мир, швейная, швейные, вышивальная, вышивальные, вязальная, вязальные, машинка, машина, машинки, машины, оверлок, оверлоки,  шитье, вышивка, вязание, купить, интернет, магазин, pfaff, brother, janome, bernina, husqvarna, huskystar, viking, оверлок, строчка, петля, челнок, стежок, ткань, рукав" />
            </Head>
            <main className="page-wrapper">
                <Topbar hideSignIn={hideSignIn} hideCartNotice={hideCartNotice} />
                {contentWrapper({title, children, ...props})}
            </main>

            { /* Back To Top Button */ }
            <a className="btn-scroll-top" href="#top" data-scroll data-fixed-element>
                <span className="btn-scroll-top-tooltip text-muted fs-sm me-2">Начало</span>
                <i className="btn-scroll-top-icon ci-arrow-up" />
            </a>
            { /* Toast: Added to Cart */ }
            <div className="toast-container position-absolute p-3 bottom-0 start-50 translate-middle-x">
                <div className="toast" id="cart-toast" data-delay="5000" role="alert" aria-live="assertive" aria-atomic="true">
                    <div className="toast-header bg-success text-white">
                        <i className="ci-basket me-2"></i>
                        <span className="fw-medium me-auto">Added to cart!</span>
                        <button type="button" className="btn-close btn-close-white ms-2" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                    <div className="toast-body">This item has been added to your cart.</div>
                </div>
            </div>
        </>
    )
}

BaseLayout.defaultProps = {
    hideCartNotice: false,
    contentWrapper: ({children}) => children
};
