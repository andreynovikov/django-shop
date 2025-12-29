import { IconCamera } from '@tabler/icons-react';

export default function NoImage({size=160, ...props}) {
    const style = {
        width: size,
        height: size,
        padding: Math.floor(size / 4)
    }

    return (
        <IconCamera style={style} {...props} />
    )
}
