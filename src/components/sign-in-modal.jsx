import { forwardRef, useImperativeHandle, useRef } from 'react';

import LoginForm from '@/components/login-form';

export default forwardRef(function SignInModal(props, ref) {
    const modalRef = useRef();

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

    useImperativeHandle(ref, () => ({
        showModal,
        hideModal
    }));

    return (
        <div className="modal fade" ref={modalRef} id="signin-modal" tabIndex="-1" role="dialog">
            <div className="modal-dialog modal-dialog-centered" role="document">
                <div className="modal-content">
                    <div className="modal-header bg-secondary">
                        <ul className="nav nav-tabs card-header-tabs" role="tablist">
                            <li className="nav-item">
                                <a className="nav-link fw-medium active" href="#signin-tab" data-bs-toggle="tab" role="tab" aria-selected="true">
                                    <i className="ci-unlocked me-2 mt-n1" />
                                    Вход
                                </a>
                            </li>
                            <li className="nav-item">
                                <a className="nav-link fw-medium" href="#signup-tab" data-bs-toggle="tab" role="tab" aria-selected="false">
                                    <i className="ci-user me-2 mt-n1" />
                                    Регистрация
                                </a>
                            </li>
                        </ul>
                        <button className="btn-close" type="button" data-bs-dismiss="modal" onClick={hideModal} aria-label="Close"></button>
                    </div>
                    <div className="modal-body tab-content py-4">
                        <div className="tab-pane fade show active" id="signin-tab">
                            <LoginForm embedded={true} ctx="login" hideModal={hideModal} />
                        </div>
                        <div className="tab-pane fade" id="signup-tab">
                            {/*
                            {% include "shop/user/_registration_form.html" with embedded=True %}
                             */
                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
});
