import BaseLayout from './base'
import { pageContentWrapper } from './page-content-wrapper'

export { pageContentWrapper }

export default function PageLayout({
  titleAddon = null,
  dark = false,
  overlapped = false,
  contentWrapper = pageContentWrapper,
  ...props
}) {
  return (
    <BaseLayout
      titleAddon={titleAddon}
      dark={dark}
      overlapped={overlapped}
      contentWrapper={contentWrapper}
      {...props} />
  )
};
