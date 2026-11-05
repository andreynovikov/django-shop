import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import RegistrationForm from '@/components/user/registration-form'

export const metadata: Metadata = {
  title: 'Добро пожаловать',
}

export default async function RegisterPage() {
  return pageContentWrapper({
    title: 'Добро пожаловать',
    children: (
      <div className="mb-6 px-3 py-4 lg:py-6">
        <div className="md:mx-auto md:w-1/2">
          <RegistrationForm />
        </div>
      </div>
    ),
  })
}