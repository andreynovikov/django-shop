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
          <div className="container text-start">
            <div className="row">
              <div className={article.image ? "col-sm-8" : "col"}>
                <h3 className="display-6">{article.title}</h3>
                <div className="mb-1 text-muted">{moment(article.publish_date).format('LL')}</div>
                <div className="text-lg" dangerouslySetInnerHTML={{ __html: article.content }}></div>
              </div>
              {article.image && (
                <div className="col-sm-4">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img className="img-fluid" src={article.image} alt={article.title} />
                </div>
              )}
            </div>
          </div>
        </SwiperSlide>
      ))}
    </Swiper>
  )
}
