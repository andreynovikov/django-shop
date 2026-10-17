import { Metadata } from 'next'

import LoginForm from '@/components/login-form'

export const metadata: Metadata = {
  title: 'Добро пожаловать',
}

interface PageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export default async function LoginPage({ searchParams }: PageProps) {
  const params = await searchParams
  const phone = params.phone as string | undefined
  const ctx = params.ctx as string | undefined ?? 'login'

  return (
    <div className="container py-3 py-lg-4 my-4">
      <div className="row justify-content-md-center">
        <div className="col-md-6">
          <h2 className="h4 mb-3">Добро пожаловать</h2>
          {/* @ts-expect-error TODO: fix typing after LoginForm converted to TypeScript */}
          <LoginForm key={phone} ctx={ctx} phone={phone} />
        </div>
      </div>
    </div>
  )
}