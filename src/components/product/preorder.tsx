import { useState } from 'react'

import { Toast } from '@base-ui/react/toast'

import { ButtonLoading } from '@/components/loading'
import LoginForm from '@/components/login-form'
import { Modal, ModalBody } from '@/components/ui/modal'

import { createPreorder } from '@/lib/queries'
import { useSession } from '@/lib/session'
import { Product } from '@/lib/types'

export default function ProductPreorder({ product }: { product: Product }) {
  const [show, setShow] = useState(false)
  const [isPending, setIsPending] = useState(false)
  const { user, status } = useSession()

  const toastManager = Toast.useToastManager()

  const showModal = () => {
    setShow(true)
  }

  const hideModal = () => {
    setShow(false)
  }

  const registerPreorder = async () => {
    setIsPending(true)
    await createPreorder(product.id)
    hideModal()
    setIsPending(false)
    toastManager.add({
      description: "Запрос зарегистрирован",
    })
  }

  return (
    <>
      <a className="btn btn-success btn-shadow d-block w-100" onClick={showModal} style={{ cursor: 'pointer' }}>
        <i className="ci-loudspeaker fs-lg me-2" />Сообщить о поступлении в интернет-магазин
      </a>
      <Modal show={show} onHide={hideModal}>
        <ModalBody>
          {status === 'authenticated' ? (
            <>
              <div className="mb-2">{user?.name || "Уважаемый покупатель"}!</div>
              <p>
                В случае оформления запроса, мы свяжемся с Вами, как только <b>{product.title}</b> появится у нас на складе.
                Если данный товар ожидается нескоро, мы свяжемся с Вами в ближайшее время и предложим альтернативные варианты.
              </p>
              <button className="btn btn-primary btn-shadow d-block w-100 mt-4" onClick={registerPreorder} disabled={isPending}>
                <i className="fs-lg me-2 ci-basket-alt" />Оформить запрос о поступлении
                {isPending && <ButtonLoading />}
              </button>
            </>
          ) : (
            <LoginForm embedded="preorder" ctx="preorder" />
          )}
        </ModalBody>
      </Modal>
    </>
  )
}