import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import { loadNews } from '@/lib/queries'

import moment from 'moment'

export const metadata: Metadata = {
  title: 'Новости',
}

// Static, the backend revalidates it when news are saved
export default async function NewsPage() {
  const news = await loadNews()

  return pageContentWrapper({
    title: 'Новости',
    children: (
      <section className="pb-5">
        <div className="container">
          {news.map((article) => (
            <div className="pb-4" key={article.id}>
              <h2 className="mb-5 text-muted">{article.title}</h2>
              <div className="mb-2 text-muted">{moment(article.publish_date).format('LL')}</div>
              {article.image && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img className="rounded mx-auto mb-2 d-block" style={{ maxHeight: "200px" }} src={article.image} alt={article.title} />
              )}
              <div className="text-lg" dangerouslySetInnerHTML={{ __html: article.content }}></div>
            </div>
          ))}
        </div>
      </section>
    )
  })
}
