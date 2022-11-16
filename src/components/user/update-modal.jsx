import { useState, forwardRef, useImperativeHandle, createRef, useRef } from 'react';

import UpdateForm from '@/components/user/update-form';

export default forwardRef(function UserUpdateModal(props, ref) {
    const [formReady, setFormReady] = useState(false);

    const formRef = createRef();
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
        <div className="modal fade" ref={modalRef} tabIndex="-1" role="dialog">
            <div className="modal-dialog modal-dialog-centered" role="document">
                <div className="modal-content">
                    <div className="modal-body">
                        <UpdateForm embedded ref={formRef} onReady={() => setFormReady(true)} onUpdated={hideModal} />
                    </div>
                    { formReady && (
                        <div className="modal-footer">
                            <button type="button" class="btn btn-secondary btn-sm" onClick={hideModal}>Закрыть</button>
                            <button type="submit" class="btn btn-primary btn-sm" onClick={() => formRef.current.submit()}>Сохранить</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
});
