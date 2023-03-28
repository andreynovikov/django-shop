import BaseLayout from './base';

export const pageContentWrapper = ({title, titleAddon, dark, overlapped, children}) => {
    return (
        <>
            <div className={`bg-${dark ? 'dark' : 'secondary'} ${overlapped ? 'page-title-overlap pt-4' : 'py-4'}`}>
                <div className="container d-lg-flex justify-content-between py-2 py-lg-3">
                    <div className="order-lg-2 mb-3 mb-lg-0 pt-lg-2">
                    </div>
                    <div className="order-lg-1 pe-lg-4 text-center text-lg-start">
                        <h1 className={`h3 mb-0 text-${dark ? 'light' : 'dark'}`}>{title}</h1>
                        { titleAddon }
                    </div>
                </div>
            </div>
            {children}
        </>
    )
};

export default function PageLayout(props) {
    return (
        <BaseLayout {...props} />
    )
};

PageLayout.defaultProps = {
    titleAddon: null,
    dark: false,
    overlapped: false,
    contentWrapper: pageContentWrapper
};