import Spinner from 'react-bootstrap/Spinner';

export default function Loading({className}) {
    return (
        <div className={className}>
            <Spinner animation="border" role="status">
                <span className="visually-hidden">Загрузка...</span>
            </Spinner>
        </div>
    )
}
