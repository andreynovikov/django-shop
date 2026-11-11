'use client'

import { useState } from 'react'
import { useIsMutating } from '@tanstack/react-query'

import { ButtonLoading } from '@/components/loading'
import UserTopbar from '@/components/user/topbar'
import UpdateForm, { updateFormMutationKey } from '@/components/user/update-form'
import { buttonClass } from '@/components/ui/button'

const FORM_ID = 'user-update-form'

export default function UserProfile() {
  const [formReady, setFormReady] = useState(false)
  const isSaving = useIsMutating({ mutationKey: updateFormMutationKey(FORM_ID) }) > 0

  return (
    <>
      <UserTopbar>
        <div className="me-4 flex w-full text-center text-overlap">&nbsp;</div>
      </UserTopbar>
      <UpdateForm id={FORM_ID} onReady={() => setFormReady(true)} />
      {formReady && (
        <>
          <hr className="mt-6 mb-4" />
          <div className="text-end">
            <button className={buttonClass()} type="submit" form={FORM_ID} disabled={isSaving}>
              Сохранить
              {isSaving && <ButtonLoading />}
            </button>
          </div>
        </>
      )}
    </>
  )
}
