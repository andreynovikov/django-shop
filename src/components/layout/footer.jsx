import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPhone, faEnvelope, faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import { faVk, faYoutube } from '@fortawesome/free-brands-svg-icons';

import SvgIcon from '@/components/svg-icon';

export default function Footer() {
    return (
        <footer className="main-footer">
            <div className="py-6 bg-gray-300 text-muted">
                <div className="container">
                    <div className="row">
                        <div className="col-lg-4 mb-5 mb-lg-0 text-center text-sm-start">
                            <img src="/i/logo.svg" className="mb-3" style={{maxWidth: "100px"}} alt="Family" />
                            <div>Больше интересного в социальных сетях:</div>
                            <ul className="list-inline">
			                    <li className="list-inline-item">
                                    <a className="text-muted text-hover-primary text-xl" href="https://vk.com/sew.world" target="_blank" rel="noreferrer" title="VK">
                                        <FontAwesomeIcon icon={faVk} />
                                    </a>
                                </li>
                                <li className="list-inline-item">
                                    <a className="text-muted text-hover-primary text-xl" href="https://www.youtube.com/c/ШвейныйМирРоссия/" target="_blank" rel="noreferrer" title="YouTube">
                                        <FontAwesomeIcon icon={faYoutube} />
                                    </a>
                                </li>
                            </ul>
                        </div>
                        <div className="col-lg-4 col-md-12 mb-5 mb-lg-0 d-flex justify-content-center justify-content-sm-start">
                            <SvgIcon id="customer-support-1" className="svg-icon service-icon" />
                            <div className="service-text text-dark mb-3">
                                <h6 className="text-nowrap">
                                    <FontAwesomeIcon icon={faPhone} fixedWidth className="me-2" />
                                    +7 495 744-00-87
                                </h6>
				                <h6 className="text-nowrap">
                                    <i className="fa-brands fa-whatsapp fa-fw me-2" />{ /* we use font icon as SVG icon is too thin and there is no way to make it bolder */ }
                                    +7 985 766-56-75
                                </h6>
                                <h6 className="text-nowrap">
                                    <FontAwesomeIcon icon={faEnvelope} fixedWidth className="me-2" />
                                    <a className="text-muted fw-normal" href="mailto:info@thsm.ru">info@thsm.ru</a>
                                </h6>
                            </div>
                        </div>
                        <div className="col-lg-4">
                            <h6 className="text-uppercase text-dark mb-3">Новинки и скидки</h6>
                            <p className="mb-3">Подпишитесь на новости и мы сообщим о наших специальных предложениях:</p>
                            <form method="POST" action="https://cp.unisender.com/ru/subscribe?hash=6ag87sp95se3dnxjfcqpuuzuecea35ueiscjkuqxbo9kgbqc8oy3y" name="subscribtion_form" id="newsletter-form">
                                <div className="input-group mb-3">
                                    <input className="form-control bg-transparent border-secondary border-end-0" type="email" placeholder="Ваш адрес Email" aria-label="Ваш адрес Email" name="email" />
                                    <div className="input-group-append">
                                        <button className="btn btn-outline-secondary border-start-0" type="submit">
                                            <FontAwesomeIcon icon={faPaperPlane} className="text-lg text-dark" />
                                        </button>
                                    </div>
                                </div>
			                    <input type="hidden" name="charset" value="UTF-8" />
				                <input type="hidden" name="default_list_id" value="15181421" />
				                <input type="hidden" name="overwrite" value="2" />
				                <input type="hidden" name="is_v5" value="1" />
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            <div className="py-4 font-weight-light bg-gray-800 text-gray-300">
                <div className="container text-center text-sm-start">
                    <p className="mb-sm-0">&copy; 2022 Family House LLP</p>
                </div>
            </div>
        </footer>
    )
}

