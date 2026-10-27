import { useState } from 'react'

import { Tabs } from '@base-ui/react/tabs'

import { Modal, ModalHeader, ModalBody } from '@/components/ui/modal'
import LoginForm from '@/components/login-form'
import RegistrationForm from '@/components/user/registration-form'

interface SignInModalProps {
  ctx: string
  show: boolean
  onHide: () => void
}

const tabClassName = (state: Tabs.Tab.State) => 'nav-link fw-medium' + (state.active ? ' active' : '')

export default function SignInModal({ ctx: modalCtx, show, onHide }: SignInModalProps) {
  const [key, setKey] = useState('signin')
  const [ctx, setCtx] = useState('login')
  const [phone, setPhone] = useState('')

  const onRegistrationComplete = (phone: string) => {
    setCtx('reg')
    setPhone(phone)
    setKey('signin')
  }

  return (
    <Modal show={show} onHide={onHide}>
      <Tabs.Root value={key} onValueChange={(value) => setKey(value)}>
        <ModalHeader>
          <Tabs.List className="nav nav-tabs card-header-tabs">
            <div className="nav-item">
              <Tabs.Tab value="signin" className={tabClassName}>
                <i className="ci-unlocked me-2 mt-n1" />
                Вход
              </Tabs.Tab>
            </div>
            <div className="nav-item">
              <Tabs.Tab value="signup" className={tabClassName}>
                <i className="ci-user me-2 mt-n1" />
                Регистрация
              </Tabs.Tab>
            </div>
          </Tabs.List>
        </ModalHeader>
        <ModalBody>
          <Tabs.Panel value="signin" keepMounted>
            <LoginForm key={phone} embedded={modalCtx} ctx={ctx} phone={phone} hideModal={onHide} />
          </Tabs.Panel>
          <Tabs.Panel value="signup" keepMounted>
            <RegistrationForm embedded={modalCtx} onComplete={onRegistrationComplete} />
          </Tabs.Panel>
        </ModalBody>
      </Tabs.Root>
    </Modal>
  )
}
