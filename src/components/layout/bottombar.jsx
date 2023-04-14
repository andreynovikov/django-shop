import Link from 'next/link';

export default function BottomBar() {
    return (
        <footer className="footer bg-dark pt-5">
            <div className="container">
                <div className="d-md-flex justify-content-between">
                    <div className="pb-4 fs-xs text-light opacity-50 text-center text-md-start">
                        &copy; 2003-2023 Швейный Мир. Все права защищены.{' '}
                        <span className="opacity-50">
                            Developed by <a className="text-light" href="https://andreynovikov.info/" target="_blank" rel="noopener">Andrey Novikov</a>.
                            Design by <a className="text-light" href="https://createx.studio/" target="_blank" rel="noopener">Createx Studio</a>.
                        </span>
                    </div>
                    <div className="widget widget-links widget-light pb-4">
                        <ul className="widget-list d-flex flex-wrap justify-content-center justify-content-md-start">
                            { /* <li class="nav-item"><a class="nav-link" href="{% url 'sales_actions' %}">Акции</a></li> */ }
                            <li className="widget-list-item ms-4">
                                <Link className="widget-list-link fs-ms" href="/pages/articles/">
                                    Справочные материалы
                                </Link>
                            </li>
                            <li className="widget-list-item ms-4">
                                <Link className="widget-list-link fs-ms" href="/blog/entries">
                                    Блог
                                </Link>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </footer>
    )
}
