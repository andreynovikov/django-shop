import BaseLayout from '@/components/layout/base'

export default function Custom404() {
  return <div className="m-5 text-center">
    <div className="fs-2">К сожалению, запрашиваемая вами страница не найдена</div>
    <div className="mt-5 text-secondary" style={{fontSize: "10rem"}}>404</div>
  </div>
}

Custom404.getLayout = function getLayout(page) {
    return (
        <BaseLayout title="Страница не найдена">
            {page}
        </BaseLayout>
    )
}