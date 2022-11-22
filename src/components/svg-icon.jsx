export const spritePath = '/vendor/sell/orion-svg-sprite.svg';

export default function SvgIcon({id, ...props}) {
    return (
        <svg {...props}>
            <use href={`${spritePath}#${id}`} />
        </svg>
    )
}
