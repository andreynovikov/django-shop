'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { Toast } from '@base-ui/react/toast'
import { IconBasket, IconSpeakerphone } from '@tabler/icons-react'

import { ButtonLoading } from '@/components/loading'
import LoginForm from '@/components/user/login-form'
import { Modal, ModalBody } from '@/components/ui/modal'
import { buttonClass } from '@/components/ui/button'

import { createPreorder } from '@/lib/queries'
import { useSession } from '@/lib/session'
import { Product } from '@/lib/types'

export default function ProductPreorder({ product }: { product: Product }) {
  const [show, setShow] = useState(false)
  const { user, status } = useSession()

  const toastManager = Toast.useToastManager()

  const showModal = () => {
    setShow(true)
  }

  const hideModal = () => {
    setShow(false)
  }

  const { mutate: registerPreorder, isPending } = useMutation({
    mutationFn: () => createPreorder(product.id),
    onSuccess: () => {
      hideModal()
      toastManager.add({
        description: "Запрос зарегистрирован",
      })
    },
    onError: (error) => {
      console.error(error)
    }
  })

  return (
    <>
      <button type="button" className={buttonClass({ variant: 'success', block: true, shadow: true })} onClick={showModal}>
        <IconSpeakerphone size={18} stroke={1.5} className="me-2" />Сообщить о поступлении
      </button>
      <Modal show={show} onHide={hideModal}>
        <ModalBody>
          {status === 'authenticated' ? (
            <>
              <div className="mb-2">{user?.name || "Уважаемый покупатель"}!</div>
              <p className="mb-4">
                В случае оформления запроса, мы свяжемся с Вами, как только <b>{product.title}</b> появится у нас на складе.
                Если данный товар ожидается нескоро, мы свяжемся с Вами в ближайшее время и предложим альтернативные варианты.
              </p>
              <button className={`${buttonClass({ block: true, shadow: true })} mt-6`} onClick={() => registerPreorder()} disabled={isPending}>
                <IconBasket size={18} stroke={1.5} className="me-2" />Оформить запрос о поступлении
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