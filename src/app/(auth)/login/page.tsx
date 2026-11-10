import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import LoginForm from '@/components/user/login-form'

export const metadata: Metadata = {
  title: 'Добро пожаловать',
}

export default async function LoginPage() {
  return pageContentWrapper({
    title: 'Добро пожаловать',
    children: (
      <div className="mb-6 px-3 py-4 lg:py-6">
        <div className="md:mx-auto md:w-1/2">
          <LoginForm ctx="login" />
        </div>
      </div>
    ),
  })
}
