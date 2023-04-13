export default function NoImage({size, ...props}) {
    const style = {
        width: size,
        height: size,
        padding: Math.floor(size / 4)
    }

    return (
        <span style={style} {...props}>&#8709;</span>
    )
}

NoImage.defaultProps = {
    size: 160
}
