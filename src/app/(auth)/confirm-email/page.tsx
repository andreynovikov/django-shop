import { Metadata } from 'next'

import ConfirmEmail from '@/components/user/confirm-email'

export const metadata: Metadata = {
  title: 'Подтверждение адреса',
  robots: { index: false },
}

// Opened from the link in the email that confirms the user's address
export default async function ConfirmEmailPage() {
  return (
    <div className="container my-6 py-4 lg:py-6">
      <div className="md:flex md:justify-center">
        <div className="md:w-1/2">
          <h2 className="mb-4 text-h4">Подтверждение адреса</h2>
          <ConfirmEmail />
        </div>
      </div>
    </div>
  )
}
