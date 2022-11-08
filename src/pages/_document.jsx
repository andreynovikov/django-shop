import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
    return (
        <Html>
            <Head>
                { /* Required because of https://github.com/vercel/next.js/issues/32645 */ }
                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;700&display=swap" />
            </Head>
            <body>
                <Main />
                <NextScript />
            </body>
        </Html>
    )
}
