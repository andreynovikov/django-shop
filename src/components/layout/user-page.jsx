import Layout from './layout';
import UserSidebar from '@/components/user/sidebar';

const userPageContentWrapper = ({children}) => {
    return (
        <div className="row">
            <UserSidebar />
            <section className="col-lg-8">
                {children}
            </section>
        </div>
    )
};

export default function UserPageLayout({hideTitleBorder=true, contentWrapper=userPageContentWrapper, ...props}) {
    return (
        <Layout hideTitleBorder={hideTitleBorder} contentWrapper={contentWrapper} {...props} />
    )
};
