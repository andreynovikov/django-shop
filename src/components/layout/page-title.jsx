export default function PageTitle({title, description}) {
    return (
        <>
            <h1>{ title }</h1>
            { description && <p>{ description }</p> }
        </>
    )
}
