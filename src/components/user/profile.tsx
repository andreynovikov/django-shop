'use client'

import { useState } from 'react'

import UserTopbar from '@/components/user/topbar'
import UpdateForm from '@/components/user/update-form'
import { buttonClass } from '@/components/ui/button'

export default function UserProfile() {
  const [formReady, setFormReady] = useState(false)

  return (
    <>
      <UserTopbar>
        <div className="me-4 flex w-full text-center text-overlap">&nbsp;</div>
      </UserTopbar>
      <UpdateForm id="user-update-form" onReady={() => setFormReady(true)} />
      {formReady && (
        <>
          <hr className="mt-6 mb-4" />
          <div className="text-end">
            <button className={buttonClass()} type="submit" form="user-update-form">Сохранить</button>
          </div>
        </>
      )}
    </>
  )
}
