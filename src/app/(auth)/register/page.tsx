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
      <div className="container py-3 py-lg-4 mb-4">
        <div className="row justify-content-md-center">
          <div className="col-md-6">
            <RegistrationForm />
          </div>
        </div>
      </div>
    ),
  })
}