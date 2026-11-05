import { buttonClass } from '@/components/ui/button'

export default function Footer() {
    return (
        <footer className="relative">
            <div className="absolute bottom-0 w-full px-3 pb-2 text-center">
                <form method="POST" action="https://cp.unisender.com/ru/subscribe?hash=6ag87sp95se3dnxjfcqpuuzuecea35ueiscjkuqxbo9kgbqc8oy3y">
                    <div className="mb-2 font-bold text-white">
                        Оставьте свой e-mail и узнайте первыми о скидках и новинках:
                    </div>
                    <div className="mb-2">
                        <label className="me-2 font-bold text-white">E-mail</label>
                        <input className="w-full max-w-[300px] border border-gray-400 bg-white px-0.5 text-body" type="text" name="email" />
                    </div>
                    <div className="mb-2">
                        <input className="align-middle" type="checkbox" />
                        <span className="ms-2 text-xs text-white">
                            Я согласен с политикой конфиденциальности
                        </span>
                    </div>
                    <button className={`${buttonClass({ variant: 'warning', size: 'sm' })} font-bold`} type="submit">Подписаться</button>
                    <input type="hidden" name="charset" value="UTF-8" />
                    <input type="hidden" name="default_list_id" value="15181421" />
                    <input type="hidden" name="overwrite" value="2" />
                    <input type="hidden" name="is_v5" value="1" />
                </form>
                <div className="mt-2 lg:mt-4">
                    <a className="block sm:inline" href="http://www.singer.com">&copy;2004-2025 Singer Sourcing Limited LLC</a>
                    <span className="hidden sm:inline">|</span>
                    <a className="block sm:inline" href="http://www.sewing-world.ru">Представитель в России - &laquo;Швейный Мир&raquo;</a>
                    <span className="hidden sm:inline">|</span>
                    <a className="block sm:inline" href="mailto:info@singer.ru">info@singer.ru</a>
                </div>
            </div>
        </footer>
    )
}
