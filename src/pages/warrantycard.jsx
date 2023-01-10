import { useState } from 'react';

import Layout from '@/components/layout';

import { getWarrantyCard } from '@/lib/queries';

export default function WarrantyCard() {
    const [error, setError] = useState({});

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError({});
        const code = e.currentTarget['code'].value;
        console.log(code);
        if (code === '') {
            setError({'code': ["Укажите серийный номер изделия"]});
            return;
        }
        await getWarrantyCard(code)
            .then(function (response) {
                console.log(response.data);
                const newWindow = window.open();
                newWindow.document.write(response.data.html);
                newWindow.document.title = `Гарантийный талон №${code}`;
            })
            .catch(function (error) {
                if (error?.response?.data && error.response.headers['content-type'].toLowerCase() === 'application/json')
                    setError(error.response.data);
                else
                    setError({'non_field_errors': [error.response?.statusText || error.message]});
            });
    };

    return (
        <div className="container mb-5">
            <div className="row justify-content-md-center">
                <div className="col-md-6">
                    <form onSubmit={handleSubmit} noValidate>
                        { error && 'non_field_errors' in error && error['non_field_errors'].map((err, index) => (
                            <>
                                <div className="is-invalid text-danger">Ошибка: </div>
                                <div className="invalid-feedback mt-0 mb-3" key={index}>{ err }</div>
                            </>
                        ))}
                        <div className="mb-3">
                            <label for="id_code">Серийный номер:</label>
                            <input
                                type="text"
                                name="code"
                                className={"form-control" + ((error && 'code' in error) ? " is-invalid" : "")}
                                maxLength={100}
                                required
                                id="id_code" />
                            { error && 'code' in error && error['code'].map((err, index) => (
                                <div className="invalid-feedback" key={index}>{ err }</div>
                            ))}
                            <small className="form-text text-muted">Серийный номер можно найти на корпусе изделия или в гарантийном талоне</small>
                        </div>
                        <input type="submit" className="btn btn-primary" value="Распечатать" />
                    </form>
                </div>
            </div>
        </div>
    )
}

WarrantyCard.getLayout = function getLayout(page) {
    return (
        <Layout title="Печать гарантийного талона">
            {page}
        </Layout>
    )
}
