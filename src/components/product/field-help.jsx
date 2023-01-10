import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { usePopper } from 'react-popper';

import { pageKeys, loadPage } from '@/lib/queries';

const fields = [
    'km_class', 'km_font', 'sw_hoopsize', 'sw_datalink', 'sm_shuttletype', 'sm_stitchwidth', 'sm_stitchlenght',
    'sm_maxi', 'sm_stitchquantity', 'sm_buttonhole', 'sm_alphabet', 'sm_dualtransporter', 'sm_platformlenght',
    'sm_freearm', 'sm_feedwidth', 'sm_footheight', 'sm_constant', 'sm_speedcontrol', 'sm_needleupdown', 'sm_threader',
    'sm_spool', 'sm_presscontrol', 'sm_power', 'sm_organizer', 'sm_autostop', 'sm_ruler', 'sm_cover', 'sm_advisor',
    'sm_startstop', 'sm_kneelift', 'sm_diffeed', 'sm_easythreading', 'sm_needles'
];

export default function FieldHelp({field}) {
    const [visible, setVisible] = useState(false);
    const [referenceElement, setReferenceElement] = useState(null);
    const [popperElement, setPopperElement] = useState(null);
    const [arrowElement, setArrowElement] = useState(null);

    const { styles, attributes, update } = usePopper(referenceElement, popperElement, {
        placement: 'auto',
        modifiers: [
            { name: 'arrow', options: { element: arrowElement } },
            { name: 'offset', options: { offset: [0, 10] } },
        ],
    });

    const uri = ['help', field];

    const { data, isSuccess } = useQuery(pageKeys.detail(uri), () => loadPage(uri), {
        enabled: visible
    });

    useEffect(() => {
        if (isSuccess && update !== null)
            update();
    }, [isSuccess, update]);

    useEffect(() => {
        if (popperElement && referenceElement) {
            const handleClickOutside = (e) => {
                const target = e.composedPath?.()?.[0] || e.target;
                if (!popperElement.contains(target) && !referenceElement.contains(target))
                    setVisible(false);
            };
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [popperElement, referenceElement]);

    const handleClick = () => {
        setVisible(!visible);
    };

    if (!fields.includes(field))
        return null;

    return (
        <>
            <button type="button" ref={setReferenceElement} onClick={handleClick} className="btn btn-link p-0 ps-1">
                <img src="/i/icons/more_icon.png" className="opacity-50" alt="Подсказка" />
            </button>
            { visible && (
                <div className="popover bs-popover-auto sw-field-help" ref={setPopperElement} style={styles.popper} {...attributes.popper}>
                    <div className="popover-arrow" ref={setArrowElement} style={styles.arrow} {...attributes.arrow} />
                    <div className="popover-body">
                        { isSuccess ? (
                            <div dangerouslySetInnerHTML={{__html: data.content }}></div>
                        ) : (
                            <div className="spinner-border" role="status"><span className="visually-hidden">Загрузка...</span></div>
                        )}
                    </div>
                </div>
            )}
        </>
    )
}
