import { useState, useEffect, useReducer, forwardRef, useImperativeHandle, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { IconCircleCheck } from '@tabler/icons-react';

import { useSession } from '@/lib/session';
import { userKeys, getUserForm, updateUser } from '@/lib/queries';
import phoneInputMask from '@/lib/phone-input-mask';

export default forwardRef(function UpdateForm({embedded, onReady, onUpdated}, ref) {
    const [ready, setReady] = useState(false);
    const [updated, setUpdated] = useState(false);
    const [error, setError] = useState(false);
    const queryClient = useQueryClient();

    const { user, status } = useSession();

    const [formData, setFormData] = useReducer((state, update) => {
        return {...state, ...update}
    }, {});

    const { data: form, isSuccess } = useQuery({
        queryKey: userKeys.form(),
        queryFn: () => getUserForm(),
        onError: (error) => {
            console.log(error);
        }
    });

    useEffect(() => {
        if (status === 'authenticated' && isSuccess) {
            const formDefaults = form.reduce((data, field) => {
                data[field.name] = '';
                return data;
            }, {});
            setFormData({...formDefaults, ...user, ...formData}); // otherwise form is reset on each window focus
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [user, status, form, isSuccess]);

    useEffect(() => {
        if (isSuccess && status === 'authenticated' && Object.keys(formData).length > 0) {
            setReady(true);
            onReady()
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [isSuccess, status, formData]);

    useEffect(() => {
        if (updated) {
            const timer = setTimeout(() => setUpdated(false), 5 * 1000);
            return () => {
                clearTimeout(timer);
            };
        }
    }, [updated]);

    const updateUserMutation = useMutation({
        mutationFn: () => updateUser(user.id, formData),
        onSuccess: () => {
            queryClient.invalidateQueries(userKeys.details());
        }
    });

    const formRef = useRef();
    const phoneRef = useRef();

    useEffect(() => {
        if (ready && phoneRef.current && !!!phoneRef.current.inputmask)
            phoneInputMask.mask(phoneRef.current)
    }, [ready, phoneRef])

    const validatePhone = () => {
        return phoneRef.current && phoneRef.current.inputmask.isComplete();
    }

    const handleChange = (e) => {
        setFormData({[e.target.name]: e.target.value});
    };

    const handleSubmit = async (e) => {
        if (e)
            e.preventDefault();
        if (!validatePhone(formRef.current.elements.phone.value)) {
            console.error("error");
            setError({phone: ["Введите корректный номер"]});
        } else {
            updateUserMutation.mutate(undefined, {
                onSuccess: () => {
                    if (onUpdated !== undefined)
                        onUpdated();
                    else
                        setUpdated(true);
                },
                onError: (error) => {
                    console.error(error);
                    if (error.response && error.response.data)
                        setError(error.response.data);
                }
            });
        }
    };

    useImperativeHandle(ref, () => ({
        submit: handleSubmit
    }));

    if (!ready)
        return <div>Loading...</div>

    return (
        <form ref={formRef} noValidate>
            { updated && (
                <div className="alert alert-success d-flex" role="alert">
                    <IconCircleCheck stroke={1.5} className="me-3" />
                    <div>Изменения успешно сохранены.</div>
                </div>
            )}

            <div className="row gx-4 gy-3">
                { form.map((field) => (
                    <div className={`col-${ embedded ? "12" : "md-6"}`} key={field.id}>
                        <label className="form-label" htmlFor={ field.id }>{ field.label }:</label>
                        { field.name === "phone" ? (
                            <div className="input-group">
                                <span className="input-group-text bg-light">+7</span>
                                <input
                                    ref={phoneRef}
                                    className={"form-control" + ((error && field.name in error) ? " is-invalid" : "")}
                                    id={field.id}
                                    name={field.name}
                                    value={formData[field.name]}
                                    onChange={handleChange}
                                    type="tel"
                                    placeholder="(999) 111-22-33"
                                    autoComplete="phone"
                                    required={field.required} />
                                { error && field.name in error && error[field.name].map((err, index) => (
                                    <div className="invalid-feedback" key={index}>{ err }</div>
                                ))}
                            </div>
                        ) : (
                            <>
                                <input
                                    className={"form-control" + ((error && field.name in error) ? " is-invalid" : "")}
                                    id={field.id}
                                    name={field.name}
                                    value={formData[field.name]}
                                    onChange={handleChange}
                                    required={field.required} />
                                { error && field.name in error && error[field.name].map((err, index) => (
                                    <div className="invalid-feedback" key={index}>{ err }</div>
                                ))}
                            </>
                        )}
                        { field.text && <small className="form-text text-muted">{ field.help }</small> }
                    </div>
                ))}
            </div>
        </form>
    )
});
