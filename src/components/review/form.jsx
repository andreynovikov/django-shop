import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import UserUpdateModal from '@/components/user/update-modal';

import { useSession } from '@/lib/session';
import { reviewKeys, getReviewForm, loadProductReview, createProductReview, updateProductReview } from '@/lib/queries';

export default function ReviewForm({product, review: reviewId}) {
    const [updated, setUpdated] = useState(false);
    const [error, setError] = useState({});
    const queryClient = useQueryClient();
    const modalRef = useRef();
    const { user } = useSession();

    const { data: form, isSuccess: isFormSuccess } = useQuery({
        queryKey: reviewKeys.form(product.id),
        queryFn: () => getReviewForm(product.id),
    });

    const { data: review, isSuccess: isReviewSuccess } = useQuery({
        queryKey: reviewKeys.detail(product.id, reviewId),
        queryFn: () => loadProductReview(product.id, reviewId),
        enabled: reviewId !== undefined,
    });

    useEffect(() => {
        if (updated) {
            const timer = setTimeout(() => setUpdated(false), 5 * 1000);
            return () => {
                clearTimeout(timer);
            };
        }
    }, [updated]);

    const createReviewMutation = useMutation({
        mutationFn: (data) => createProductReview(product.id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: reviewKeys.list(product.id)});
        }
    });

    const updateReviewMutation = useMutation({
        mutationFn: (data) => updateProductReview(product.id, reviewId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: reviewKeys.detail(product.id, reviewId)});
            queryClient.invalidateQueries({queryKey: reviewKeys.list(product.id)});
        }
    });

    const handleChange = (e) => {
        const field = e.currentTarget.name;
        if (error && field in error) {
            setError(Object.keys(error).reduce(function (filtered, key) {
                if (key !== field)
                    filtered[key] = error[key];
                return filtered;
            }, {}));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const config = {
            onSuccess: () => {
                setUpdated(true);
            },
            onError: (error) => {
                console.error(error);
                if (error.response?.data && error.response.headers['content-type'].toLowerCase() === 'application/json')
                    setError(error.response.data);
            }
        };
        if (reviewId)
            updateReviewMutation.mutate(formData, config);
        else
            createReviewMutation.mutate(formData, config);
    };

    if (!isFormSuccess || (reviewId !== undefined && !isReviewSuccess))
        return <div>Loading...</div>

    return (
        <>
            { review && !review.is_public && (
                <div className="alert alert-accent mb-3 fs-sm" role="alert">Ваш отзыв в настоящее время находится на проверке</div>
            )}

            <h3 className="h4 pb-2">{ reviewId ? "Изменить" : "Оставить" } отзыв</h3>

            { user?.username === '' && (
                <>
                    <UserUpdateModal ref={modalRef} />
                    <div className="alert alert-warning d-flex" role="alert">
                        <div className="alert-icon">
                            <i className="ci-announcement" />
                        </div>
                        <div>
                            Вы можете{' '}
                            <a className="alert-link" onClick={() => modalRef.current.showModal()} style={{cursor:'pointer'}}>указать</a>
                            {' '}псевдоним, если не хотите, чтобы отображалось Ваше реальное имя.
                        </div>
                    </div>
                </>
            )}

            <form noValidate onSubmit={handleSubmit}>
                { updated && (
                    <div className="alert alert-success d-flex" role="alert">
                        <div className="alert-icon"><i className="ci-check-circle" /></div>
                        <div>Изменения успешно сохранены.</div>
                    </div>
                )}

                <div className="row gx-4 gy-3">
                    { form.map((field) => (
                        <div style={{display: (field.widget === 'HiddenInput' || field.name === 'honeypot') ? "none" : "initial"}} key={field.id}>
                            { field.widget !== 'HiddenInput' && (
                                <label className="form-label" htmlFor={ field.id }>
                                    { field.label }{ field.required && <span className="text-danger">*</span> }
                                </label>
                            )}
                            { field.widget === 'HiddenInput' ? (
                                <input
                                    type="hidden"
                                    name={field.name}
                                    value={field.value}
                                    required={field.required} />
                            ) : field.widget === 'Select' ? (
                                <select
                                    className={"form-select" + ((error && field.name in error) ? " is-invalid" : "")}
                                    id={field.id}
                                    name={field.name}
                                    defaultValue={review?.[field.name].value || review?.[field.name]}
                                    onChange={handleChange}
                                    required={field.required}>
                                    { field.choices.map((choice) => (
                                        <option value={choice[0]} key={choice[0]}>
                                            {choice[1]}
                                            {' '}
                                            {choice[0] && <>({choice[0]})</>}
                                        </option>
                                    ))}
                                </select>
                            ) : field.widget === 'Textarea' ? (
                                <textarea
                                    className={"form-control" + ((error && field.name in error) ? " is-invalid" : "")}
                                    id={field.id}
                                    name={field.name}
                                    defaultValue={review?.[field.name]}
                                    rows={field.attrs?.rows || 5}
                                    maxLength={field.attrs?.maxlength || 5000}
                                    required={field.required} />
                            ) : (
                                <input
                                    className={"form-control" + ((error && field.name in error) ? " is-invalid" : "")}
                                    id={field.id}
                                    name={field.name}
                                    defaultValue={review?.[field.name] || field.value}
                                    required={field.required} />
                            )}
                            { error && field.name in error && error[field.name].map((err, index) => (
                                <div className="invalid-feedback" key={index}>{ err }</div>
                            ))}
                            { field.text && <small className="form-text text-muted">{ field.help }</small> }
                        </div>
                    ))}
                </div>
                <button className="btn btn-primary btn-shadow d-block mt-4" type="submit">Опубликовать отзыв</button>
            </form>
        </>
    )
}
