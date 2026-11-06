import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import LoginPageForm from '@/components/user/login-page-form'

export const metadata: Metadata = {
  title: 'Добро пожаловать',
}

export default async function LoginPage() {
  return pageContentWrapper({
    title: 'Добро пожаловать',
    children: (
      <div className="container py-3 py-lg-4 mb-4">
        <div className="row justify-content-md-center">
          <div className="col-md-6">
            <LoginPageForm />
          </div>
        </div>
      </div>
    ),
  })
}
