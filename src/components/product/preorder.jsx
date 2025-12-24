import { useState } from 'react'

import { Toast } from '@base-ui/react/toast'
import Modal from 'react-bootstrap/Modal'

import LoginForm from '@/components/login-form'

import { createPreorder } from '@/lib/queries'
import { useSession } from '@/lib/session'

export default function ProductPreorder({ product }) {
  const [show, setShow] = useState(false)
  const { user, status } = useSession()

  const toastManager = Toast.useToastManager()

  const showModal = () => {
    setShow(true)
  }

  const hideModal = () => {
    setShow(false)
  }

  const registerPreorder = async () => {
    await createPreorder(product.id)
    hideModal()
    toastManager.add({
      description: "Запрос зарегистрирован",
    })
  }

  return (
    <>
      <a className="btn btn-success btn-shadow d-block w-100" onClick={showModal} style={{ cursor: 'pointer' }}>
        <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        <i className="ci-loudspeaker fs-lg me-2" />Сообщить о поступлении
      </a>
      <Modal show={show} onHide={hideModal} centered>
        <Modal.Body>
          {status === 'authenticated' ? (
            <>
              <div className="mb-2">{user?.name || "Уважаемый покупатель"}!</div>
              <p>
                В случае оформления запроса, мы свяжемся с Вами, как только <b>{product.title}</b> появится у нас на складе.
                Если данный товар ожидается нескоро, мы свяжемся с Вами в ближайшее время и предложим альтернативные варианты.
              </p>
              <a className="btn btn-primary btn-shadow d-block w-100 mt-4" onClick={registerPreorder}>
                <i className="fs-lg me-2 ci-basket-alt" />Оформить запрос о поступлении
              </a>
            </>
          ) : (
            <LoginForm embedded={true} ctx="preorder" />
          )}
        </Modal.Body>
      </Modal>
    </>
  )
}