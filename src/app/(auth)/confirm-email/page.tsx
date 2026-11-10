import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import ConfirmEmail from '@/components/user/confirm-email'

export const metadata: Metadata = {
  title: 'Подтверждение адреса',
  robots: { index: false },
}

// Opened from the link in the email that confirms the user's address
export default async function ConfirmEmailPage() {
  return pageContentWrapper({
    title: 'Подтверждение адреса',
    children: (
      <div className="mb-6 px-3 py-4 lg:py-6">
        <div className="md:mx-auto md:w-1/2">
          <ConfirmEmail />
        </div>
      </div>
    ),
  })
}