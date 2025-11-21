export default function TopSidebar({ children }) {
  return (
    <div className="d-none d-lg-flex justify-content-between align-items-center pt-lg-3 pb-4 pb-lg-5 mb-lg-3">
      {children}
    </div>
  )
}
