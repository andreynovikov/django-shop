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
      <div className="container mb-6 py-4 lg:py-6">
        <div className="md:mx-auto md:w-1/2">
          <LoginPageForm />
        </div>
      </div>
    ),
  })
}
