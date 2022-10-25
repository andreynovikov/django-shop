import PageLayout, { pageContentWrapper } from './page';
import UserSidebar from '@/components/user/sidebar';

const userPageContentWrapper = ({title, dark, overlapped, children}) => {
    return pageContentWrapper({
        title,
        dark,
        overlapped,
        children: (
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="row">
                    <UserSidebar />
                    <section className="col-lg-8">
                        {children}
                    </section>
                </div>
            </div>
        )
    });
};

export default function UserPageLayout(props) {
    return (
        <PageLayout {...props} />
    )
};

UserPageLayout.defaultProps = {
    dark: true,
    overlapped: true,
    contentWrapper: userPageContentWrapper
};
