export default function PageTitle({title, description}) {
    return (
        <section className="hero">
            <div className="container">
                { /*
                <!-- Breadcrumbs -->
                <ol class="breadcrumb justify-content-center">
                    <li class="breadcrumb-item"><a href="index.html">Home</a></li>
                    <li class="breadcrumb-item active">Text page        </li>
                </ol>
                  */
                }
                <div className="hero-content mt-3 pb-5 text-center">
                    <h1 className="hero-heading">{ title }</h1>
                    { description && (
                        <div className="row">
                            <div className="col-xl-8 offset-xl-2">
                                <p className="lead text-muted" dangerouslySetInnerHTML={{__html: description }}></p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    )
}
