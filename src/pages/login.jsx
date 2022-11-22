import Layout from '@/components/layout';
import LoginForm from '@/components/user/login-form';
import PageTitle from '@/components/layout/page-title';

export default function Login({ctx, phone}) {
    return (
        <>
            <PageTitle title="Добро пожаловать" />
            <section>
                <div className="container mb-5">
                    <div className="row justify-content-md-center">
                        <div className="col-md-6">
                            <LoginForm ctx={ctx} phone={phone} />
                        </div>
                    </div>
                </div>
            </section>
        </>
    )
}

Login.defaultProps = {
    ctx: 'login',
    phone: ''
}

Login.getLayout = function getLayout(page) {
    return (
        <Layout title="Добро пожаловать">
            {page}
        </Layout>
    )
}

export async function getServerSideProps(context) {
    return {
        props: context.query || {}
    }
}

