import { useState } from 'react'

import Head from 'next/head'

import UserPageLayout from '@/components/layout/user-page'
import UserTopbar from '@/components/user/topbar'
import UpdateForm from '@/components/user/update-form'

export default function Profile() {
  const [formReady, setFormReady] = useState(false)

  return (
    <>
      <Head>
        <meta name="robots" content="noindex" />
      </Head>
      <UserTopbar>
        <div className="d-flex w-100 text-light text-center me-3">&nbsp;</div>
      </UserTopbar>
      <UpdateForm id="user-update-form" onReady={() => setFormReady(true)} />
      {formReady && (
        <>
          <hr className="mt-4 mb-3" />
          <div className="text-end">
            <button className="btn btn-primary" type="submit" form="user-update-form">Сохранить</button>
          </div>
        </>
      )}
    </>
  )
}

Profile.getLayout = function getLayout(page) {
  const breadcrumbs = [
    {
      label: 'Личный кабинет'
    }
  ]
  return (
    <UserPageLayout title="Профиль" breadcrumbs={breadcrumbs}>
      {page}
    </UserPageLayout>
  )
}
