import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { usePopper } from 'react-popper';

import { pageKeys, loadPage } from '@/lib/queries';

export default function Popover({page, anchorElement, onClose, children}) {
    const [popperElement, setPopperElement] = useState(null);
    const [arrowElement, setArrowElement] = useState(null);

    const { styles, attributes, update } = usePopper(anchorElement, popperElement, {
        placement: 'auto',
        strategy: 'fixed',
        modifiers: [
            { name: 'arrow', options: { element: arrowElement } },
            { name: 'offset', options: { offset: [0, 10] } },
        ],
    });

    const uri = page ? page.slice(1, -1).split('/') : null;
    console.log(anchorElement);
    console.log(uri)

    const { data, isSuccess } = useQuery({
        queryKey: pageKeys.detail(uri),
        queryFn: () => loadPage(uri),
        enabled: anchorElement !== null && uri !== null
    });

    useEffect(() => {
        if (isSuccess && update !== null)
            update();
    }, [isSuccess, update]);

    useEffect(() => {
        if (popperElement && anchorElement) {
            const handleClickOutside = (e) => {
                const target = e.composedPath?.()?.[0] || e.target;
                if (!popperElement.contains(target) && !anchorElement.contains(target)) {
                    onClose();
                }
            };
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [popperElement, anchorElement, onClose]);

    return (
        anchorElement && (
            <div className="popover bs-popover-auto sw-popover" ref={setPopperElement} style={styles.popper} {...attributes.popper}>
                <div className="popover-arrow" ref={setArrowElement} style={styles.arrow} {...attributes.arrow} />
                <div className="popover-body">
                    { children ? (
                        children
                    ) : isSuccess ? (
                        <div dangerouslySetInnerHTML={{__html: data.content }}></div>
                    ) : (
                        <div className="spinner-border" role="status"><span className="visually-hidden">Загрузка...</span></div>
                    )}
                </div>
            </div>
        )
    )
}
