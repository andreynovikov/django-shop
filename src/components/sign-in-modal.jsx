import { useState, useEffect, forwardRef, useImperativeHandle, useRef } from 'react';

import LoginForm from '@/components/login-form';
import RegistrationForm from '@/components/user/registration-form';

export default forwardRef(function SignInModal({ctx: modalCtx}, ref) {
    const [ctx, setCtx] = useState('login');
    const [phone, setPhone] = useState('');

    const modalRef = useRef();
    const tabRef = useRef();

    useEffect(() => {
        if (phone !== '') {
            const tabEle = tabRef.current;
            const bsTab = bootstrap.Tab.getOrCreateInstance(tabEle);
            bsTab.show();
        }
    }, [phone]);

    const showModal = () => {
        const modalEle = modalRef.current;
        const bsModal = new bootstrap.Modal(modalEle, {
            backdrop: 'static',
            keyboard: false
        });
        bsModal.show();
    }

    const hideModal = () => {
        const modalEle = modalRef.current;
        const bsModal= bootstrap.Modal.getInstance(modalEle);
        bsModal.hide();
    }

    const onRegistrationComplete = (phone) => {
        setCtx('reg');
        setPhone(phone);
    };

    useImperativeHandle(ref, () => ({
        showModal,
        hideModal
    }));

    return (
        <div className="modal fade" ref={modalRef} tabIndex="-1" role="dialog">
            <div className="modal-dialog modal-dialog-centered" role="document">
                <div className="modal-content">
                    <div className="modal-header bg-secondary">
                        <ul className="nav nav-tabs card-header-tabs" role="tablist">
                            <li className="nav-item">
                                <a className="nav-link fw-medium active" href={`#${modalCtx}-signin-tab`} data-bs-toggle="tab" role="tab" aria-selected="true" ref={tabRef}>
                                    <i className="ci-unlocked me-2 mt-n1" />
                                    Вход
                                </a>
                            </li>
                            <li className="nav-item">
                                <a className="nav-link fw-medium" href={`#${modalCtx}-signup-tab`} data-bs-toggle="tab" role="tab" aria-selected="false">
                                    <i className="ci-user me-2 mt-n1" />
                                    Регистрация
                                </a>
                            </li>
                        </ul>
                        <button className="btn-close" type="button" data-bs-dismiss="modal" onClick={hideModal} aria-label="Close"></button>
                    </div>
                    <div className="modal-body tab-content py-4">
                        <div className="tab-pane fade show active" id={`${modalCtx}-signin-tab`}>
                            <LoginForm embedded={modalCtx} ctx={ctx} phone={phone} hideModal={hideModal} />
                        </div>
                        <div className="tab-pane fade" id={`${modalCtx}-signup-tab`}>
                            <RegistrationForm embedded={modalCtx} onComplete={onRegistrationComplete} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
});
