export default function NoImage({size, block, ...props}) {
    const style = block ? {
        width: size,
        fontSize: size
    } : {
        width: size,
        height: size,
        fontSize: Math.floor(size / 2),
        padding: Math.floor(size / 4)
    }

    return (
        <i className={(block ? "d-block mx-auto" : "d-inline-block") + " ci-camera text-muted"} style={style} {...props} />
    )
}

NoImage.defaultProps = {
    size: 200,
    block: false
}
