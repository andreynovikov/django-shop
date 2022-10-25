import { useState, useEffect, useReducer, forwardRef, useImperativeHandle, useRef } from 'react';
import { useRouter } from 'next/router';
import Script from 'next/script';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import { withSession, userKeys, getUserForm, loadUser, updateUser } from '@/lib/queries';

export default forwardRef(function UpdateForm({embedded, onReady}, ref) {
    const [ready, setReady] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(false);
    const router = useRouter();
    const queryClient = useQueryClient();

    const { data: session, status } = useSession({
        required: true,
        onUnauthenticated() {
            router.push({
                pathname: '/login',
                query: { callbackUrl: router.asPath }
            });
        },
    });

    const [formData, setFormData] = useReducer((state, update) => {
        return {...state, ...update}
    }, {});

    const { data: form, isSuccess: isFormSuccess } = useQuery(
        userKeys.form(),
        () => getUserForm(),
        {
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const { data: user, isSuccess: isUserSuccess } = useQuery(
        userKeys.detail(session?.user),
        () => withSession(session, loadUser, session?.user),
        {
            enabled: status === 'authenticated'
        }
    );

    useEffect(() => {
        if (isUserSuccess && isFormSuccess) {
            const formDefaults = form.reduce((data, field) => {
                data[field.name] = '';
                return data;
            }, {});
            setFormData({...formDefaults, ...user, ...formData}); // otherwise form is reset on each window focus
        }
    }, [user, isUserSuccess, form, isFormSuccess]);

    useEffect(() => {
        if (isFormSuccess && isUserSuccess && Object.keys(formData).length > 0) {
            setReady(true);
            onReady()
        }
    }, [isFormSuccess, isUserSuccess, formData]);

    useEffect(() => {
        if (success) {
            const timer = setTimeout(() => setSuccess(false), 5 * 1000);
            return () => {
                clearTimeout(timer);
            };
        }
    }, [success]);

    const updateUserMutation = useMutation(() => withSession(session, updateUser, session.user, formData), {
        onSuccess: () => {
            queryClient.invalidateQueries(userKeys.details());
        }
    });

    const formRef = useRef();
    const phoneRef = useRef();

    const validatePhone = (value) => {
        return phoneRef.current && phoneRef.current.inputmask.isComplete();
    }

    const handleChange = (e) => {
        setFormData({[e.target.name]: e.target.value});
    };

    const handleSubmit = async () => {
        if (!validatePhone(formRef.current.elements.phone.value)) {
            console.error("error");
            setError({phone: ["Введите корректный номер"]});
        } else {
            updateUserMutation.mutate(undefined, {
                onSuccess: (data) => {
                    console.error("success");
                    console.error(data);
                    setSuccess(true);
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

    const setupInputMask = () => {
        if (window && window.Inputmask && phoneRef.current && !!!phoneRef.current.inputmask) {
            window.Inputmask({
                mask: ["(999) 999-99-99", "* (999) 999-99-99"],
                definitions: {
                    "*": { validator: "[78]" }
                },
                onBeforePaste: function(pastedValue, opts) {
                    return pastedValue.replace("+7", "");
                },
                onBeforeMask: function(value, opts) {
                    return value.replace("+7", "");
                },
                oncomplete: function() {
                    var value = this.inputmask.unmaskedvalue();
                    if (value.length > 10) {
                        value = value.substr(1);
                        this.inputmask.setValue(value);
                    }
                },
                keepStatic: true
            }).mask(phoneRef.current);
        }
    };

    if (!ready)
        return <div>Loading...</div>

    return (
        <form ref={formRef} noValidate>
            { success && (
                <div className="alert alert-success d-flex" role="alert">
                    <div className="alert-icon"><i className="ci-check-circle" /></div>
                    <div>Изменения успешно сохранены.</div>
                </div>
            )}

            <div className="row gx-4 gy-3">
                { form.map((field) => (
                    <div className={`col-${ embedded ? "12" : "md-6"}`} key={field.id}>
                        <label className="form-label" htmlFor={ field.id }>{ field.label }:</label>
                        { field.name === "phone" ? (
                            <div className="input-group">
                                <span className="input-group-text bg-secondary">+7</span>
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
            <Script
                id="inputmask"
                src="/js/inputmask.js"
                onReady={setupInputMask}
                onLoad={setupInputMask} />
        </form>
    )
});
