export default function NoImage({size=160, ...props}) {
    const style = {
        width: size,
        height: size,
        padding: Math.floor(size / 4)
    }

    return (
        <span style={style} {...props}>&#8709;</span>
    )
}
