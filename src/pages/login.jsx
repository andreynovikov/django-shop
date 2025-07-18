import BaseLayout from '@/components/layout/base';
import LoginForm from '@/components/login-form';

export default function Login({ctx='login', phone=''}) {
    return (
        <div className="container py-3 py-lg-4 my-4">
            <div className="row justify-content-md-center">
                <div className="col-md-6">
                    <h2 className="h4 mb-3">Добро пожаловать</h2>
                    <LoginForm ctx={ctx} phone={phone} />
                </div>
            </div>
        </div>
    )
}

Login.getLayout = function getLayout(page) {
    return (
        <BaseLayout title="Добро пожаловать" hideSignIn>
            {page}
        </BaseLayout>
    )
}

export async function getServerSideProps(context) {
    return {
        props: context.query || {}
    }
}

