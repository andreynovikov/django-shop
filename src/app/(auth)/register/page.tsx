import { Metadata } from 'next'

import RegistrationForm from '@/components/user/registration-form'

export const metadata: Metadata = {
  title: 'Добро пожаловать',
}

export default async function RegisterPage() {
  return (
    <div className="container my-6 py-4 lg:py-6">
      <div className="md:flex md:justify-center">
        <div className="md:w-1/2">
          <h2 className="mb-4 text-h4">Добро пожаловать</h2>
          <RegistrationForm />
        </div>
      </div>
    </div>
  )
}