import Layout from '@/components/layout';
import RegistrationForm from '@/components/user/registration-form';
import PageTitle from '@/components/layout/page-title';

export default function Register() {
    return (
        <>
            <PageTitle title="Регистрация" />
            <section>
                <div className="container mb-5">
                    <div className="row justify-content-md-center">
                        <div className="col-md-6">
                            <RegistrationForm />
                        </div>
                    </div>
                </div>
            </section>
        </>
    )
}

Register.getLayout = function getLayout(page) {
    return (
        <Layout title="Регистрация">
            {page}
        </Layout>
    )
}
