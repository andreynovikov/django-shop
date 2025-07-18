import { useQuery } from '@tanstack/react-query';

import axios from 'axios';

async function loadAvatar(gravatar, name, size) {
    const d = name.startsWith('+7') ? 'mp' : '404';
    return axios.get(gravatar + '&d=' + d, {
        responseType: 'arraybuffer'
    }).then((response) => {
        // const buffer = URL.createObjectURL(response.data); - with responseType: 'blob'
        const buffer = Buffer.from(response.data, 'binary').toString('base64');
        return `data:${response.headers['content-type'].toLowerCase()};base64,${buffer}`;
    }).catch(() => {
        return axios.get('https://ui-avatars.com/api/', {
            params: {
                size: size,
                bold: 'true',
                color: '4e54c8',
                background: 'fff',
                name: name
            },
            responseType: 'arraybuffer'
        }).then((response) => {
            const buffer = Buffer.from(response.data, 'binary').toString('base64');
            return `data:${response.headers['content-type'].toLowerCase()};base64,${buffer}`;
        });
    });
}

export default function UserAvatar({gravatar, name, size=50, border=false}) {
    const { data: avatar } = useQuery({
        queryKey: ['avatars', { gravatar, name, size }],
        queryFn: () => loadAvatar(gravatar, name, size),
        placeholderData: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
        staleTime: Infinity
    });

    /* eslint-disable @next/next/no-img-element */
    return (
        <img className={"rounded-circle" + (border ? " border border-1" : "")} width={size} height={size} src={avatar} alt={ name } />
    )
}
