import { IconBrandYoutube, IconBrandVk, IconBrandWhatsapp, IconMail, IconPhone, IconSend } from '@tabler/icons-react';

import SvgIcon from '@/components/svg-icon';
import { buttonClass } from '@/components/ui/button';

const contactClass = 'mb-2 font-bold leading-[1.1] whitespace-nowrap'
const contactIconClass = 'me-2 inline align-middle'

export default function Footer() {
    return (
        <footer>
            <div className="bg-gray-300 py-24 text-muted">
                <div className="container">
                    <div className="grid gap-x-6 gap-y-12 lg:grid-cols-3">
                        <div className="text-center sm:text-start">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src="/i/logo.svg" className="mx-auto mb-4 max-w-25 sm:mx-0" alt="Family" />
                            <div>Больше интересного в социальных сетях:</div>
                            <ul className="mt-1 flex justify-center gap-2 sm:justify-start">
                                <li>
                                    <a className="text-muted hover:text-primary" href="https://vk.com/sew.world" target="_blank" rel="noreferrer" title="VK">
                                        <IconBrandVk />
                                    </a>
                                </li>
                                <li>
                                    <a className="text-muted hover:text-primary" href="https://www.youtube.com/c/ШвейныйМирРоссия/" target="_blank" rel="noreferrer" title="YouTube">
                                        <IconBrandYoutube />
                                    </a>
                                </li>
                            </ul>
                        </div>
                        <div className="flex justify-center sm:justify-start">
                            <SvgIcon id="customer-support-1" className="svg-icon me-6 size-12 shrink-0 stroke-2" />
                            <div className="text-dark">
                                <h6 className={contactClass}>
                                    <IconPhone size={20} className={contactIconClass} />
                                    +7 495 744-00-87
                                </h6>
                                <h6 className={contactClass}>
                                    <IconBrandWhatsapp size={20} className={contactIconClass} />
                                    +7 985 766-56-75
                                </h6>
                                <h6 className={contactClass}>
                                    <IconMail size={20} className={contactIconClass} />
                                    <a className="font-normal text-muted" href="mailto:info@thsm.ru">info@thsm.ru</a>
                                </h6>
                            </div>
                        </div>
                        <div>
                            <h6 className="mb-4 font-bold leading-[1.1] tracking-widest text-dark uppercase">Новинки и скидки</h6>
                            <p className="mb-4">Подпишитесь на новости и мы сообщим о наших специальных предложениях:</p>
                            <form method="POST" action="https://cp.unisender.com/ru/subscribe?hash=6ag87sp95se3dnxjfcqpuuzuecea35ueiscjkuqxbo9kgbqc8oy3y" name="subscribtion_form" id="newsletter-form">
                                <div className="mb-4 flex">
                                    <input
                                        className="block w-full min-w-0 flex-auto border border-e-0 border-secondary bg-transparent px-3 py-2.5 text-body placeholder:text-muted focus:border-gray-700 focus:outline-none"
                                        type="email"
                                        placeholder="Ваш адрес Email"
                                        aria-label="Ваш адрес Email"
                                        name="email" />
                                    <button className={`${buttonClass({ variant: 'outline-secondary' })} border-s-0`} type="submit" aria-label="Подписаться">
                                        <IconSend className="text-dark" />
                                    </button>
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
            <div className="bg-gray-800 py-6 text-gray-300">
                <div className="container text-center sm:text-start">
                    <p>&copy; 2022 Family House LLP</p>
                </div>
            </div>
        </footer>
    )
}
