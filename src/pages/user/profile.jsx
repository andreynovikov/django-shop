import { useState, createRef } from 'react';

import UserPageLayout from '@/components/layout/user-page';
import UpdateForm from '@/components/user/update-form';

export default function Profile() {
    const [formReady, setFormReady] = useState(false);

    const formRef = createRef();

    return (
        <>
            <UpdateForm ref={formRef} onReady={() => setFormReady(true)} />
            { formReady && (
                <>
                    <hr className="mt-4 mb-3" />
                    <div className="text-end">
                        <button className="btn btn-primary" type="submit" onClick={() => formRef.current.submit()}>Сохранить</button>
                    </div>
                </>
            )}
        </>
    )
}

Profile.getLayout = function getLayout(page) {
    return (
        <UserPageLayout title="Профиль">
            {page}
        </UserPageLayout>
    )
}
