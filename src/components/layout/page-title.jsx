export default function PageTitle({title, description, border}) {
    return (
        <div className="mt-3 mb-2" style={ border ? {borderBottom: "2px solid #D7D2CB"} : {}}>
            <h1>{ title }</h1>
            { description && <p>{ description }</p> }
        </div>
    )
}

PageTitle.defaultProps = {
    border: true
}
