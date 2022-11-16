function getStarClassName(star, value, classAddon) {
    var modifier = '';
    if (star <= value)
        modifier = '-filled';
    else if (star <= (value + 0.7))
        modifier = '-half';
    return `ci-star${modifier} active ${classAddon ? classAddon : "star-rating-icon"}`;
}

export default function ReviewRating({value, classAddon}) {
    return (
        <div className="star-rating">
            <i class={getStarClassName(1, value, classAddon)} />
            <i class={getStarClassName(2, value, classAddon)} />
            <i class={getStarClassName(3, value, classAddon)} />
            <i class={getStarClassName(4, value, classAddon)} />
            <i class={getStarClassName(5, value, classAddon)} />
        </div>
    )
}
