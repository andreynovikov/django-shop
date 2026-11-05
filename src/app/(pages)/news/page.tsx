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
      <section className="container pb-12">
        {news.map((article) => (
          <div className="pb-6" key={article.id}>
            <h2 className="mb-12 text-3xl leading-[1.1] font-bold text-muted lg:text-[2.7rem]">{article.title}</h2>
            <div className="mb-2 text-muted">{moment(article.publish_date).format('LL')}</div>
            {article.image && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img className="mx-auto mb-2 max-h-50 w-auto" src={article.image} alt={article.title} />
            )}
            <div className="backend-content text-lg" dangerouslySetInnerHTML={{ __html: article.content }}></div>
          </div>
        ))}
      </section>
    )
  })
}
