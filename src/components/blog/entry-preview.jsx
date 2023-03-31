import Link from 'next/link';

import BlogEntryAuthor from '@/components/blog/entry-author';

export default function BlogEntryPreview({entry, last}) {
    const previewContent = () => {
        return entry.content.preview.replace('<!--more-->', `
            <a href="${entry.urls.canonical}" class="blog-entry-meta-link fw-medium">[читать далее]</a>
        `)
    };

    return (
        <article className={"blog-list pb-4 mb-5" + (!last && " border-bottom")}>
            <div className="blog-start-column">
                <div className="d-flex align-items-center fs-sm pb-2 mb-1">
                    <BlogEntryAuthor entry={entry} />
                </div>
                <h2 className="h5 blog-entry-title">
                    <Link href={entry.urls.canonical}>{ entry.title }</Link>
                </h2>
            </div>
            <div className="blog-end-column">
                { /* <a className="blog-entry-thumb mb-3" href="blog-single.html"><img src="img/blog/02.jpg" alt="Post" /></a> */ }
                <div className="d-flex justify-content-between mb-1">
                    <div className="fs-sm text-muted pe-2 mb-2">
                        in{' '}
                        <a href='#' className='blog-entry-meta-link'>Shopping</a>
                        ,{' '}
                        <a href='#' className='blog-entry-meta-link'>Personal finance</a>
                    </div>
                    <div className="font-size-sm mb-2">
                        {entry.tags.map((tag) => (
                            <a className="btn-tag ms-2" href="#" key={tag}>#{ tag }</a>
                        ))}
                    </div>
                </div>
                <div className="fs-sm">
                    <div dangerouslySetInnerHTML={{__html: previewContent() }}></div>
                </div>
            </div>
        </article>
    )
}
