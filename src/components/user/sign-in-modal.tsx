import { useState } from 'react'

import { Tabs } from '@base-ui/react/tabs'
import { IconLockOpen, IconUser } from '@tabler/icons-react'

import { Modal, ModalHeader, ModalBody } from '@/components/ui/modal'
import LoginForm from '@/components/user/login-form'
import RegistrationForm from '@/components/user/registration-form'

interface SignInModalProps {
  ctx: string
  show: boolean
  onHide: () => void
}

// Cartzilla's tabs: the active one is primary and underlined
const tabClass = 'relative flex items-center px-5 py-3 font-medium text-gray-700 transition-colors hover:text-primary data-active:pointer-events-none data-active:text-primary before:absolute before:bottom-0 before:left-5 before:h-px before:w-[calc(100%-2.5rem)] before:transition-colors data-active:before:bg-primary'
const tabIcon = { size: 18, stroke: 1.5, className: 'me-2' }

export default function SignInModal({ ctx: modalCtx, show, onHide }: SignInModalProps) {
  const [key, setKey] = useState('signin')

  return (
    <Modal show={show} onHide={onHide}>
      <Tabs.Root value={key} onValueChange={(value) => setKey(value)}>
        <ModalHeader>
          <Tabs.List className="-mx-5 -mt-[.3125rem] -mb-4 flex">
            <Tabs.Tab value="signin" className={tabClass}>
              <IconLockOpen {...tabIcon} />
              Вход
            </Tabs.Tab>
            <Tabs.Tab value="signup" className={tabClass}>
              <IconUser {...tabIcon} />
              Регистрация
            </Tabs.Tab>
          </Tabs.List>
        </ModalHeader>
        <ModalBody>
          {/* Base UI hides the previous panel only after its exit animation, so both forms would show for a frame */}
          <Tabs.Panel value="signin" keepMounted hidden={key !== 'signin'}>
            <LoginForm embedded={modalCtx} ctx="login" hideModal={onHide} />
          </Tabs.Panel>
          <Tabs.Panel value="signup" keepMounted hidden={key !== 'signup'}>
            {/* the user is signed in when it completes */}
            <RegistrationForm embedded={modalCtx} onComplete={onHide} />
          </Tabs.Panel>
        </ModalBody>
      </Tabs.Root>
    </Modal>
  )
}
