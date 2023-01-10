export default function Footer() {
    return (
        <footer className="position-relative">
            <div className="position-absolute bottom-0 text-center w-100 px-3 pb-2">
                <form method="POST" action="https://cp.unisender.com/ru/subscribe?hash=6ag87sp95se3dnxjfcqpuuzuecea35ueiscjkuqxbo9kgbqc8oy3y">
                    <div className="fw-bold text-white mb-2">
                        Оставьте свой e-mail и узнайте первыми о скидках и новинках:
                    </div>
                    <div className="mb-2">
                        <label className="fw-bold text-white me-2">E-mail</label>
                        <input type="text" name="email" />
                    </div>
                    <div className="mb-2">
                        <input type="checkbox" />
                        <span className="text-white fs-sm ms-2">
                            Я согласен с политикой конфиденциальности
                        </span>
                    </div>
                    <button className="btn btn-sm btn-warning text-white fw-bold" type="submit">Подписаться</button>
                    <input type="hidden" name="charset" value="UTF-8" />
                    <input type="hidden" name="default_list_id" value="15181421" />
                    <input type="hidden" name="overwrite" value="2" />
                    <input type="hidden" name="is_v5" value="1" />
                </form>
                <div className="mt-2 mt-lg-3">
                    <a className="d-block d-sm-inline" href="http://www.singer.com">&copy;2004-2022 Singer Sourcing Limited LLC</a>
                    <span className="d-none d-sm-inline">|</span>
                    <a className="d-block d-sm-inline" href="http://www.sewing-world.ru">Представитель в России - &laquo;Швейный Мир&raquo;</a>
                    <span className="d-none d-sm-inline">|</span>
                    <a className="d-block d-sm-inline" href="mailto:info@singer.ru">info@singer.ru</a>
                </div>
            </div>
        </footer>
    )
}
