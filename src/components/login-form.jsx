import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Script from 'next/script';
import { useQuery } from 'react-query';

import { signIn } from '@/lib/session';
import { userKeys, checkUser, normalizePhone } from '@/lib/queries';
import { useCountdown } from '@/lib/countdown';

const CODE_RESEND_DELAY = 240;

export default function LoginForm({embedded, ctx, hideModal}) {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [loginPhone, setLoginPhone] = useState('');
    const [reset, setReset] = useState(false);
    const [error, setError] = useState(false);

    const [delay, setDelay] = useState(-1);
    const [countdown, countdownText] = useCountdown(delay);

    const router = useRouter();

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
                                    setError(result.error);
                                }
                            });
                    } else {
                        setError("Пользователь с таким телефоном не зарегистрирован");
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
        return phoneRef.current && phoneRef.current.inputmask.isComplete();
    }

    const validatePassword = (value) => {
        return !!(value.match(/^(:?\d{4}|.{5,30})$/));
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(false);
        if (e.target.elements.phone) {
            if (validatePhone(e.target.elements.phone.value)) {
                setLoginPhone(normalizePhone(e.target.elements.phone.value));
            } else {
                setError("Введите корректный номер");
            }
        } else if (e.target.elements.password) {
            if (validatePassword(e.target.elements.password.value)) {
                const result = await signIn({phone: loginPhone, password});
                if (result.ok) {
                    if (embedded) {
                        if (hideModal)
                            hideModal();
                    } else {
                        router.push(router.query.callbackUrl || '/');
                    }
                } else {
                    try {
                        const error = JSON.parse(result.error);
                        console.log(error);
                        if (error.password)
                            setError(error.password);
                        else if (result.status === 401)
                            setError("Вы ввели неправильный " + (shopUser?.permanent_password ? "пароль" : "код"));
                        else if (error.non_field_errors)
                            setError(error.non_field_errors);
                        else
                            setError("Неизвестная ошибка входа");
                    } catch (e) {
                        setError(result.error);
                    }
                }
            } else {
                setError("Указан неверный " + (shopUser?.permanent_password ? "пароль" : "код"));
            }
        }
    }

    const resetPhone = () => {
        setDelay(-1);
        setLoginPhone('');
        setError(false);
    };

    const resetPassword = () => {
        setDelay(-1);
        setReset(true);
    };

    const formatPhone = (phone) => {
        return phone;
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
        <form id={`sw-${ctx}-form`} onSubmit={handleSubmit} noValidate>
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
                            className={"form-control" + (error ? " is-invalid" : "")}
                            style={embedded ? {} : {maxWidth: "20rem"}}
                            ref={passwordRef.current}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            id={`${ctx}-password-input`}
                            placeholder={ shopUser?.permanent_password ? "Пароль" : "Код из смс" }
                            required
                            autoFocus />
                        { error && <div className="invalid-feedback">{ error }</div> }
                        <div className="form-text">
                            { countdown > 180 && (
                                <span id={`${ctx}-password-help`} className="text-warning">Код выслан на указанный телефон по смс</span>
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
                    { /*
                    { ctx !== 'order' && !shopUser?.permanent_password && (
                        <>
                            { ctx === 'login' && (
                                <div className="mb-3 fs-md">Вы можете <a href="#" id="permanent-password-link">указать постоянный пароль</a>, чтобы не получать каждый раз смс</div>
                            )}
                            <div id="permanent-password-block" className="form-row{% if ctx == 'login' %} d-none{% endif %}">
                                <div className="mb-3 col-md">
                                    <label htmlFor="permanent-password-input">Постоянный пароль:</label>
                                    <input type="password" className="form-control form-control-sm" name="permanent_password" id="permanent-password-input" />
                                    <span id="permanent-password-error" class="invalid-feedback"></span>
                                    { ctx === 'reg' && (
                                        <span className="form-text">Если Вы не укажете постоянный пароль, вход будет осуществляться с помощью смс</span>
                                    )}
                                </div>
                                <div className="mb-3 col-md">
                                    <label htmlFor="permanent-password-input2">ещё раз:</label>
                                    <input type="password" className="form-control form-control-sm" name="permanent_password2" id="permanent-password-input2" />
                                    <span id="permanent-password-error2" className="invalid-feedback"></span>
                                </div>
                            </div>
                        </>
                    )}
                      */
                    }
                </>
            ) : (
                <>
                    { /* Анонимный пользователь */ }
                    <div className="mb-3">
                        <label className="lead" htmlFor={`${ctx}-phone-input`}>
                            { ctx === 'order' ? "Для продолжения у" : "У" }
                            кажите номер мобильного телефона:
                        </label>
                        <div className="input-group">
                            <span className="input-group-text bg-secondary">+7</span>
                            <input
                                type="tel"
                                name="phone"
                                className={"form-control" + (error ? " is-invalid" : "")}
                                ref={phoneRef}
                                id={`${ctx}-phone-input`}
                                placeholder="(999) 111-22-33"
                                autoComplete="phone"
                                required />
                            { error && <div className="invalid-feedback" id={`${ctx}-phone-input-error`}>{ error }</div> }
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
                    { !embedded && <i class={ "me-2 ms-n1" + (!!shopUser ? "ci-sign-in" : "ci-unlocked") } /> }
                    { !!shopUser ? "Продолжить" : "Войти" }
                </button>
            </div>
        )}
            { /*
                {% if not shop_user and not embedded %}
                <div class="mt-4 fs-md">Если Вы не совершали покупок в магазине, Вы можете <a href="{% url 'shop:register' %}{% if next %}?next={{ next }}{% endif %}">зарегистрироваться</a></div>
                {% endif %}
              */
            }
        { /*
<script type="text/javascript">
(function() {
    'use strict';

    var initializeLoginForm = function() {
        var phoneInput = document.getElementById("{{ ctx }}-phone-input");

        {% if shop_user %}
        {% if ctx != 'order' and not shop_user.permanent_password %}
        var ppwd1Input = document.getElementById("permanent-password-input");
        var ppwd2Input = document.getElementById("permanent-password-input2");
        var ppwd1Error = document.getElementById("permanent-password-error");
        var ppwd2Error = document.getElementById("permanent-password-error2");

        var validatePpwd = function() {
            var ppwd1 = ppwd1Input.value;
            var ppwd2 = ppwd2Input.value;

            if (ppwd1 != ppwd2) {
                ppwd2Error.textContent = "Пароли не совпадают";
            } else {
                ppwd2Error.textContent = "";
            }
            if (ppwd1.length > 0 && ppwd1.length < 5) {
                ppwd1Error.textContent = "Постоянный пароль должен быть не менее 5 символов";
            } else {
                ppwd1Error.textContent = "";
            }
            ppwd1Input.setCustomValidity(ppwd1Error.textContent);
            ppwd2Input.setCustomValidity(ppwd2Error.textContent);
        };
        ppwd1Input.addEventListener("input", validatePpwd);
        ppwd2Input.addEventListener("input", validatePpwd);

        {% if ctx == 'login' %}
        var ppwdLink = document.getElementById("permanent-password-link");
        ppwdLink.addEventListener("click", function() {
            var ppwdBlock = document.getElementById("permanent-password-block");
            ppwdBlock.classList.remove("d-none");
            ppwdLink.parentElement.classList.add("d-none");
            return false;
        });
        {% endif %}
        {% endif %}

        var passwordInput = document.getElementById("{{ ctx }}-password-input");
        var passwordError = document.getElementById("{{ ctx }}-password-error");
        var passwordHelp = document.getElementById("{{ ctx }}-password-help");
        var passwordReset = document.getElementById("{{ ctx }}-password-reset");

        // https://github.com/RobinHerbots/Inputmask
        Inputmask({
            mask: ["9999", "*{5,30}"],
            placeholder: ""
        }).mask(passwordInput);

        var validatePassword = function() {
            if (passwordInput.inputmask.isComplete()) {
                passwordInput.setCustomValidity("");
            } else {
                passwordInput.setCustomValidity("Введите пароль");
            }

            if (passwordError) {
                passwordError.parentNode.removeChild(passwordError);
                passwordError = null;
            }
            if (passwordHelp) {
                passwordHelp.textContent = "";
                passwordHelp.classList.add("d-none");
            }
        };
        passwordInput.addEventListener("input", validatePassword);
        passwordInput.addEventListener("paste", validatePassword);

        passwordInput.focus();
        {% endif %}
    };

})();
</script>
          */
        }
            <Script
                id="inputmask"
                src="/js/inputmask.js"
                onReady={setupInputMask}
                onLoad={setupInputMask} />
        </form>
    )
}
