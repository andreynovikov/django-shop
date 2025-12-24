import { useState, forwardRef, useImperativeHandle, useRef } from 'react'

import Modal from 'react-bootstrap/Modal'
import Nav from 'react-bootstrap/Nav'
import Tab from 'react-bootstrap/Tab'

import LoginForm from '@/components/login-form'
import RegistrationForm from '@/components/user/registration-form'

export default forwardRef(function SignInModal({ ctx: modalCtx }, ref) {
  const [show, setShow] = useState(false)
  const [key, setKey] = useState('signin')
  const [ctx, setCtx] = useState('login')
  const [phone, setPhone] = useState('')

  const modalRef = useRef()

  const showModal = () => {
    setShow(true)
  }

  const hideModal = () => {
    setShow(false)
  }

  const onRegistrationComplete = (phone) => {
    setCtx('reg')
    setPhone(phone)
    setKey('signin')
  }

  useImperativeHandle(ref, () => ({ // TODO: refactor?
    showModal,
    hideModal
  }))

  return (
    <Modal ref={modalRef} show={show} onHide={hideModal} centered>
      <Tab.Container id={`${modalCtx}-tabs`} activeKey={key} onSelect={(k) => setKey(k)}>
        <Modal.Header closeButton>
          <Nav variant="tabs" className="card-header-tabs">
            <Nav.Item>
              <Nav.Link eventKey="signin" className="fw-medium">
                <i className="ci-unlocked me-2 mt-n1" />
                Вход
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="signup" className="fw-medium">
                <i className="ci-user me-2 mt-n1" />
                Регистрация
              </Nav.Link>
            </Nav.Item>
          </Nav>
        </Modal.Header>
        <Modal.Body>
          <Tab.Content>
            <Tab.Pane eventKey="signin">
              <LoginForm key={phone} embedded={modalCtx} ctx={ctx} phone={phone} hideModal={hideModal} />
            </Tab.Pane>
            <Tab.Pane eventKey="signup">
              <RegistrationForm embedded={modalCtx} onComplete={onRegistrationComplete} />
            </Tab.Pane>
          </Tab.Content>
        </Modal.Body>
      </Tab.Container>
    </Modal>
  )
})
