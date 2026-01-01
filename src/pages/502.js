import Head from 'next/head';

const styles = {
    error: {
        fontFamily: '-apple-system, BlinkMacSystemFont, Roboto, "Segoe UI", "Fira Sans", Avenir, "Helvetica Neue", "Lucida Grande", sans-serif',
        height: '100vh',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
    },

    desc: {
        display: 'inline-block',
        textAlign: 'left',
        lineHeight: '49px',
        height: '49px',
        verticalAlign: 'middle',
    },

    h1: {
        display: 'inline-block',
        margin: 0,
        marginRight: '20px',
        padding: '0 23px 0 0',
        fontSize: '24px',
        fontWeight: 500,
        verticalAlign: 'top',
        lineHeight: '49px',
        borderRight: '1px solid rgba(0, 0, 0, .3)'
    },

    h2: {
        fontSize: '14px',
        fontWeight: 'normal',
        lineHeight: '49px',
        margin: 0,
        padding: 0,
    },
}

export default function Custom404() {
    return (
        <div style={styles.error}>
            <Head>
                <title>502: Нет связи с сервером</title>
            </Head>
            <div>
                <h1 style={styles.h1}>502</h1>
                <div style={styles.desc}>
                    <h2 style={styles.h2}>Сайт находится на обслуживании, попробуйте позже</h2>
                </div>
            </div>
        </div>
    )
}
