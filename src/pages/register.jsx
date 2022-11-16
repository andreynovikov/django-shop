import BaseLayout from '@/components/layout/base';
import RegistrationForm from '@/components/user/registration-form';

export default function Register() {
    return (
        <div className="container py-3 py-lg-4 my-4">
            <div className="row justify-content-md-center">
                <div className="col-md-6">
                    <h2 className="h4 mb-3">Добро пожаловать</h2>
                    <RegistrationForm />
                </div>
            </div>
        </div>
    )
}

Register.getLayout = function getLayout(page) {
    return (
        <BaseLayout title="Добро пожаловать" hideSignIn>
            {page}
        </BaseLayout>
    )
}
