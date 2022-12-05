import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faStar as faStarFilled, faStarHalfStroke as faStarHalf } from '@fortawesome/free-solid-svg-icons';
import { faStar } from '@fortawesome/free-regular-svg-icons';

function getStarIcon(star, value) {
    if (star <= value)
        return faStarFilled;
    else if (star <= (value + 0.7))
        return faStarHalf;
    else
        return faStar;
}

export default function ReviewRating({value}) {
    return (
        <ul className="list-inline me-2 mb-0">
            <li className="list-inline-item me-0"><FontAwesomeIcon icon={getStarIcon(1, value)} /></li>
            <li className="list-inline-item me-0"><FontAwesomeIcon icon={getStarIcon(2, value)} /></li>
            <li className="list-inline-item me-0"><FontAwesomeIcon icon={getStarIcon(3, value)} /></li>
            <li className="list-inline-item me-0"><FontAwesomeIcon icon={getStarIcon(4, value)} /></li>
            <li className="list-inline-item me-0"><FontAwesomeIcon icon={getStarIcon(5, value)} /></li>
        </ul>
    )
}
