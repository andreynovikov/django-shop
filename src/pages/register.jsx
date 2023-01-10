import Layout from '@/components/layout';
import RegistrationForm from '@/components/user/registration-form';

export default function Register() {
    return (
        <section>
            <div className="container mb-5">
                <div className="row justify-content-md-center">
                    <div className="col-md-6">
                        <RegistrationForm />
                    </div>
                </div>
            </div>
        </section>
    )
}

Register.getLayout = function getLayout(page) {
    return (
        <Layout title="Регистрация">
            {page}
        </Layout>
    )
}
