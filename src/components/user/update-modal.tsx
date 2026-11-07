import { useState } from 'react'

import { Modal, ModalBody, ModalFooter } from '@/components/ui/modal'
import UpdateForm from '@/components/user/update-form'
import { buttonClass } from '@/components/ui/button'

interface UserUpdateModalProps {
  show: boolean
  onHide: () => void
}

export default function UserUpdateModal({ show, onHide }: UserUpdateModalProps) {
  const [formReady, setFormReady] = useState(false)

  return (
    <Modal show={show} onHide={onHide} staticBackdrop>
      <ModalBody>
        <UpdateForm id="user-update-modal-form" embedded onReady={() => setFormReady(true)} onUpdated={onHide} />
      </ModalBody>
      {formReady && (
        <ModalFooter>
          <button type="button" className={buttonClass({ variant: 'secondary', size: 'sm' })} onClick={onHide}>Закрыть</button>
          <button type="submit" form="user-update-modal-form" className={buttonClass({ size: 'sm' })}>Сохранить</button>
        </ModalFooter>
      )}
    </Modal>
  )
}
