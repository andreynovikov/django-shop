import { useState } from 'react'

import Modal from 'react-bootstrap/Modal'

import UpdateForm from '@/components/user/update-form'

export default function UserUpdateModal({ show, onHide }) {
  const [formReady, setFormReady] = useState(false)

  return (
    <Modal show={show} onHide={onHide} centered backdrop="static">
      <Modal.Body>
        <UpdateForm id="user-update-modal-form" embedded onReady={() => setFormReady(true)} onUpdated={onHide} />
      </Modal.Body>
      {formReady && (
        <Modal.Footer>
          <button type="button" className="btn btn-secondary btn-sm" onClick={onHide}>Закрыть</button>
          <button type="submit" form="user-update-modal-form" className="btn btn-primary btn-sm">Сохранить</button>
        </Modal.Footer>
      )}
    </Modal>
  )
}
