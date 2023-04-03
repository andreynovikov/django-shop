import { useState, useEffect } from 'react';

export default function ScrollTopButton() {
    const [show, setShow] = useState(false);

    useEffect(() => {
        const setVisibleState = (event) => {
            setShow(event.currentTarget.pageYOffset > 600);
        };
        window.addEventListener('scroll', setVisibleState);
        return () => {
            window.removeEventListener('scroll', setVisibleState);
        };
    }, []);

    const handleScroll = () => {
        window.scrollTo({
            top: 0,
            left: 0,
            behavior: 'smooth'
        });
    };

    return (
        <button className={"btn p-0 btn-scroll-top" + (show ? " show" : "")} onClick={handleScroll}>
            <span className="btn-scroll-top-tooltip text-muted fs-sm me-2">Начало</span>
            <i className="btn-scroll-top-icon ci-arrow-up">   </i>
        </button>
    )
}
