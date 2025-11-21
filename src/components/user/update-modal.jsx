import { useState, forwardRef, useImperativeHandle, createRef, useRef } from 'react'

import Modal from 'react-bootstrap/Modal'

import UpdateForm from '@/components/user/update-form'

export default forwardRef(function UserUpdateModal(props, ref) {
  const [show, setShow] = useState(false)
  const [formReady, setFormReady] = useState(false)

  const formRef = createRef()
  const modalRef = useRef()

  const showModal = () => {
    setShow(true)
  }

  const hideModal = () => {
    setShow(false)
  }

  useImperativeHandle(ref, () => ({
    showModal,
    hideModal
  }))

  return (
    <Modal ref={modalRef} show={show} onHide={hideModal} centered backdrop="static">
      <Modal.Body>
        <UpdateForm embedded ref={formRef} onReady={() => setFormReady(true)} onUpdated={hideModal} />
      </Modal.Body>
      {formReady && (
        <Modal.Footer>
          <button type="button" class="btn btn-secondary btn-sm" onClick={hideModal}>Закрыть</button>
          <button type="submit" class="btn btn-primary btn-sm" onClick={() => formRef.current.submit()}>Сохранить</button>
        </Modal.Footer>
      )}
    </Modal>
  )
})
