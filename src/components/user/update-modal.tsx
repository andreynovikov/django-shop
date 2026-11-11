import { useState } from 'react'
import { useIsMutating } from '@tanstack/react-query'

import { ButtonLoading } from '@/components/loading'
import { Modal, ModalBody, ModalFooter } from '@/components/ui/modal'
import UpdateForm, { updateFormMutationKey } from '@/components/user/update-form'
import { buttonClass } from '@/components/ui/button'

const FORM_ID = 'user-update-modal-form'

interface UserUpdateModalProps {
  show: boolean
  onHide: () => void
}

export default function UserUpdateModal({ show, onHide }: UserUpdateModalProps) {
  const [formReady, setFormReady] = useState(false)
  const isSaving = useIsMutating({ mutationKey: updateFormMutationKey(FORM_ID) }) > 0

  return (
    <Modal show={show} onHide={onHide} staticBackdrop>
      <ModalBody>
        <UpdateForm id={FORM_ID} embedded onReady={() => setFormReady(true)} onUpdated={onHide} />
      </ModalBody>
      {formReady && (
        <ModalFooter>
          <button type="button" className={buttonClass({ variant: 'secondary', size: 'sm' })} onClick={onHide}>Закрыть</button>
          <button type="submit" form={FORM_ID} className={buttonClass({ size: 'sm' })} disabled={isSaving}>
            Сохранить
            {isSaving && <ButtonLoading />}
          </button>
        </ModalFooter>
      )}
    </Modal>
  )
}
