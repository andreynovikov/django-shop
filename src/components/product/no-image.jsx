import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCamera } from '@fortawesome/free-solid-svg-icons';

export default function NoImage({size, ...props}) {
    const style = {
        width: size,
        height: size,
        padding: Math.floor(size / 4)
    }

    return (
        <FontAwesomeIcon icon={faCamera} style={style} {...props} />
    )
}

NoImage.defaultProps = {
    size: 160
}
