import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Script from 'next/script';
import { useQuery } from 'react-query';

import { formatPhone } from '@/lib/format';
import { signIn } from '@/lib/session';
import { userKeys, checkUser, normalizePhone } from '@/lib/queries';
import { useCountdown } from '@/lib/countdown';

const CODE_RESEND_DELAY = 240;

export default function LoginForm({embedded, ctx, phone, hideModal}) {
    const [loginPhone, setLoginPhone] = useState('');
    const [reset, setReset] = useState(false);
    const [error, setError] = useState({});

    const [delay, setDelay] = useState(-1); // TODO: keep delay on page reload
    const [countdown, countdownText] = useCountdown(delay); // TODO: put in child component to optimize rendering

    const [showPermanentPassword, setShowPermanentPassword] = useState(ctx === 'reg')

    const router = useRouter();

    useEffect(() => {
        if (phone != '')
            setLoginPhone(phone);
    }, [phone]);

    const { data: shopUser, isSuccess, isFetching, refetch } = useQuery(
        userKeys.check(loginPhone),
        () => checkUser(loginPhone, reset),
        {
            enabled: !!loginPhone,
            onError: (error) => {
                if (error.response?.status === 404) {
                    if (ctx === 'order') {
                        // register user in background when making order
                        signIn({ phone: loginPhone, ctx })
                            .then(result => {
                                if (result.ok) {
                                    if (embedded && hideModal)
                                        hideModal();
                                } else {
                                    setError({ phone: result.error });
                                }
                            });
                    } else {
                        setError({ phone: "Пользователь с таким телефоном не зарегистрирован" });
                    }
                }
                console.log(error);
            }
        }
    );

    useEffect(() => {
        if (isSuccess && !isFetching) {
            setReset(false);
            if (!shopUser.permanent_password) {
                setDelay(CODE_RESEND_DELAY);
            } else {
                setDelay(0);
            }
        }
    }, [shopUser, isSuccess, isFetching]);

    useEffect(() => {
        if (reset) {
            refetch();
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [reset]);

    const phoneRef = useRef(null);
    const passwordRef = useRef(null);

    const validatePhone = () => {
        return phoneRef.current && phoneRef.current.inputmask.isComplete() ?
            {} : { phone: "Введите корректный номер" };

    };

    const validatePassword = (value) => {
        if (!!!(value.match(/^(:?\d{4}|.{5,30})$/)))
            return { password: "Указан неверный " + (shopUser?.permanent_password ? "пароль" : "код") };
        else
            return {};
    };

    const validatePermanentPasswords = (value1, value2) => {
        const err = {};
        if (value1 != value2)
            err['permanent_password2'] = "Пароли не совпадают";
        if (value1.length > 0 && value1.length < 5)
            err['permanent_password'] = "Постоянный пароль должен быть не менее 5 символов";
        return err;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError({});
        if (e.target.elements.phone) {
            const err = validatePhone();
            if (Object.keys(err).length > 0) {
                setError(err);
            } else {
                setLoginPhone(normalizePhone(e.target.elements.phone.value));
            }
        } else if (e.target.elements.password) {
            let err = validatePassword(e.target.elements.password.value);
            if (showPermanentPassword)
                err = {...err, ...validatePermanentPasswords(e.target.elements.permanent_password.value, e.target.elements.permanent_password2.value)};
            if (Object.keys(err).length > 0) {
                setError(err);
                console.log(err);
            } else {
                const credentials = {
                    phone: loginPhone,
                    password: e.target.elements.password.value,
                };
                if (showPermanentPassword && e.target.elements.permanent_password.value.length > 0)
                    credentials['permanent_password'] = e.target.elements.permanent_password.value;
                const result = await signIn(credentials);
                if (result.ok) {
                    if (embedded) {
                        if (hideModal)
                            hideModal();
                    } else {
                        router.push(router.query.callbackUrl || '/');
                    }
                } else {
                    try {
                        if (result.error?.response?.data) {
                            if (result.error.response.data.password)
                                setError({ password: result.error.response.data.password[0] });
                            else if (result.error.response.status === 401)
                                setError({ password: "Вы ввели неправильный " + (shopUser?.permanent_password ? "пароль" : "код") });
                            else if (result.error.response.data.non_field_errors)
                                setError({ password: result.error.response.data.non_field_errors[0] });
                            else
                                setError({ password: "Неизвестная ошибка входа" });
                        } else {
                            setError({ password: "Неизвестная ошибка входа" });
                        }
                    } catch (e) {
                        setError({ password: result.error.response?.statusText || result.error.message });
                    }
                }
            }
        }
    }

    const resetPhone = () => {
        setDelay(-1);
        setLoginPhone('');
        setError({});
    };

    const resetPassword = () => {
        setDelay(-1);
        setReset(true);
    };

    const setupInputMask = () => {
        if (window && window.Inputmask && phoneRef.current && !!!phoneRef.current.inputmask) {
            window.Inputmask({
                mask: ["(999) 999-99-99", "* (999) 999-99-99"],
                definitions: {
                    "*": { validator: "[78]" }
                },
                onBeforePaste: function(pastedValue) {
                    return pastedValue.replace("+7", "");
                },
                onBeforeMask: function(value) {
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

    return (
        <form onSubmit={handleSubmit} noValidate>
            { !!shopUser ? (
                <>
                    { /* Пользователь с таким телефоном уже есть, требуем подтверждение пароля */ }
                    <div className="lead mb-2">{ formatPhone(loginPhone) }</div>
                    { ctx === 'order' && (
                        <div className="form-text mt-n2 mb-3">
                            <a className="link-primary" onClick={resetPhone} style={{cursor:'pointer'}}>Указать другой телефон</a>
                        </div>
                    )}
                    <div className="mb-3 has-feedback">
                        <input
                            type="password"
                            name="password"
                            className={"form-control" + ('password' in error ? " is-invalid" : "")}
                            style={embedded ? {} : {maxWidth: "20rem"}}
                            ref={passwordRef.current}
                            id={`${embedded}${ctx}-password-input`}
                            placeholder={ shopUser?.permanent_password ? "Пароль" : "Код из смс" }
                            required
                            autoFocus />
                        { 'password' in error && <div className="invalid-feedback">{ error.password }</div> }
                        <div className="form-text">
                            { countdown > 180 && (
                                <span className="text-warning">Код выслан на указанный телефон по смс</span>
                            )}
                            { countdown > 0 && <div className="d-block">Запросить { shopUser?.permanent_password ? "пароль" : "код" } повторно можно<br/>{ countdownText }</div> }
                            { (isSuccess && delay >=0 && countdown === 0) && (
                                <div><a className="link-primary" onClick={resetPassword} style={{cursor:'pointer'}}>
                                    { shopUser?.permanent_password ? (
                                        "Сбросить забытый пароль"
                                    ) : (
                                        "Прислать код повторно"
                                    )}
                                </a></div>
                            )}
                        </div>
                    </div>
                    { ctx !== 'order' && isSuccess && !shopUser.permanent_password && (
                        showPermanentPassword ? (
                            <div className="row">
                                <div className="mb-3 col-md">
                                    <label htmlFor="permanent-password-input">Постоянный пароль:</label>
                                    <input
                                        type="password"
                                        className={"form-control form-control-sm" + ('permanent_password' in error ? " is-invalid" : "")}
                                        name="permanent_password"
                                        id="permanent-password-input" />
                                    { 'permanent_password' in error && <div className="invalid-feedback">{ error.permanent_password }</div> }
                                    { ctx === 'reg' && (
                                        <span className="form-text">Если Вы не укажете постоянный пароль, вход будет осуществляться с помощью смс</span>
                                    )}
                                </div>
                                <div className="mb-3 col-md">
                                    <label htmlFor="permanent-password-input2">ещё раз:</label>
                                    <input
                                        type="password"
                                        className={"form-control form-control-sm" + ('permanent_password2' in error ? " is-invalid" : "")}
                                        name="permanent_password2"
                                        id="permanent-password-input2" />
                                    { 'permanent_password2' in error && <div className="invalid-feedback">{ error.permanent_password2 }</div> }
                                </div>
                            </div>
                        ) : (
                            <div className="mb-3 fs-md">
                                Вы можете <a onClick={() => setShowPermanentPassword(true)}>указать постоянный пароль</a>, чтобы не получать каждый раз смс
                            </div>
                        )
                    )}
                </>
            ) : (
                <>
                    { /* Анонимный пользователь */ }
                    <div className="mb-3">
                        <label className="lead" htmlFor={`${embedded}${ctx}-phone-input`}>
                            { ctx === 'order' ? "Для продолжения у" : "У" }
                            кажите номер мобильного телефона:
                        </label>
                        <div className="input-group">
                            <span className="input-group-text bg-secondary">+7</span>
                            <input
                                type="tel"
                                name="phone"
                                className={"form-control" + ('phone' in error ? " is-invalid" : "")}
                                ref={phoneRef}
                                id={`${embedded}${ctx}-phone-input`}
                                placeholder="(999) 111-22-33"
                                autoComplete="phone"
                                required />
                            { 'phone' in error && <div className="invalid-feedback">{ error.phone }</div> }
                        </div>
                    </div>
                </>
            )}

            { ctx === 'order' ? (
                <button className="btn btn-primary btn-shadow d-block w-100 mt-4">
                    <i className={"fs-lg me-2 " + (!!shopUser ? "ci-sign-in" : "ci-basket-alt")} />Оформить заказ
                </button>
            ) : (
                <div className="text-end">
                    <button className={"btn btn-primary ms-4" + (embedded && " btn-shadow")} type="submit">
                        { !embedded && <i className={ "me-2 ms-n1" + (!!shopUser ? "ci-sign-in" : "ci-unlocked") } /> }
                        { !!shopUser ? "Продолжить" : "Войти" }
                    </button>
                </div>
            )}
            { !!!shopUser && !embedded && (
                <div className="mt-4 fs-md">
                    Если Вы не совершали покупок в магазине, Вы можете{" "}
                    <Link href={{ pathname: '/register', query: router.query }}>
                        зарегистрироваться
                    </Link>
                </div>
            )}
            <Script
                id="inputmask"
                src="/js/inputmask.js"
                onReady={setupInputMask}
                onLoad={setupInputMask} />
        </form>
    )
}

LoginForm.defaultProps = {
    embedded: ''
};
