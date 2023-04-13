export default function PageTitle({title, description}) {
    return (
        <div className="mt-3 mb-2">
            <h1>{ title }</h1>
            { description && <p>{ description }</p> }
        </div>
    )
}
