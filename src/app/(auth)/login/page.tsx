import { Metadata } from 'next'

import LoginPageForm from '@/components/user/login-page-form'

export const metadata: Metadata = {
  title: 'Добро пожаловать',
}

export default async function LoginPage() {
  return (
    <div className="container py-3 py-lg-4 my-4">
      <div className="row justify-content-md-center">
        <div className="col-md-6">
          <h2 className="h4 mb-3">Добро пожаловать</h2>
          <LoginPageForm />
        </div>
      </div>
    </div>
  )
}
