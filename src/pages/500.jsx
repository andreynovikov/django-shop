import BaseLayout from '@/components/layout/base'

export default function Custom404() {
  return <div className="m-5 text-center">
    <div className="fs-2">К сожалению, что-то пошло не так</div>
    <div className="lead mt-1">Мы постараемся исправить это как можно скорее</div>
    <div className="mt-5 text-secondary" style={{ fontSize: "10rem" }}>500</div>
  </div>
}

Custom404.getLayout = function getLayout(page) {
  return (
    <BaseLayout title="Ошибка сервера">
      {page}
    </BaseLayout>
  )
}