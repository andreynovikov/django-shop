import BaseLayout from '@/components/layout/base';
import LoginForm from '@/components/login-form';

export default function Login() {
    return (
        <div class="container py-3 py-lg-4 my-4">
            <div class="row justify-content-md-center">
                <div class="col-md-6">
                    <h2 class="h4 mb-3">Добро пожаловать</h2>
                    <LoginForm ctx="login" />
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

