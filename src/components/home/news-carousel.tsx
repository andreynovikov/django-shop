'use client'

import { Swiper, SwiperSlide } from 'swiper/react'
import { Pagination } from 'swiper/modules'

import { News } from '@/lib/types'

import moment from 'moment'

import 'swiper/css'
import 'swiper/css/pagination'

export default function NewsCarousel({ news }: { news: News[] }) {
  return (
    <Swiper autoHeight pagination={{ clickable: true }} modules={[Pagination]}>
      {news.map((article) => (
        <SwiperSlide key={article.id}>
          <div className="flex flex-col gap-6 px-3 text-start sm:flex-row">
            <div className="flex-1">
              <h3 className="mb-2 text-3xl leading-[1.1] lg:text-4xl">{article.title}</h3>
              <div className="mb-1 text-muted">{moment(article.publish_date).format('LL')}</div>
              <div className="backend-content text-lg" dangerouslySetInnerHTML={{ __html: article.content }}></div>
            </div>
            {article.image && (
              <div className="sm:w-1/3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={article.image} alt={article.title} />
              </div>
            )}
          </div>
        </SwiperSlide>
      ))}
    </Swiper>
  )
}
