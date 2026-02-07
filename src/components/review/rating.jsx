import { IconStar, IconStarFilled, IconStarHalfFilled } from '@tabler/icons-react';

function getStarIcon(star, value) {
    if (star <= value)
        return <IconStarFilled />;
    else if (star <= (value + 0.7))
        return <IconStarHalfFilled />;
    else
        return <IconStar />;
}

export default function ReviewRating({value}) {
    return (
        <ul className="list-inline me-2 mb-0">
            <li className="list-inline-item me-0">{getStarIcon(1, value)}</li>
            <li className="list-inline-item me-0">{getStarIcon(2, value)}</li>
            <li className="list-inline-item me-0">{getStarIcon(3, value)}</li>
            <li className="list-inline-item me-0">{getStarIcon(4, value)}</li>
            <li className="list-inline-item me-0">{getStarIcon(5, value)}</li>
        </ul>
    )
}
