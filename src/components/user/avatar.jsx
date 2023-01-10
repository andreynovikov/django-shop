import { useState, useEffect } from 'react';

import axios from 'axios';

export default function UserAvatar({gravatar, name, size, border, className}) {
    const [avatar, setAvatar] = useState('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=');

    useEffect(() => {
        if (gravatar !== '') {
            const d = name.startsWith('+7') ? 'mp' : '404';
            axios.get(gravatar + '&d=' + d, {
                responseType: 'arraybuffer'
            }).then((response) => {
                // const buffer = URL.createObjectURL(response.data); - with responseType: 'blob'
                const buffer = Buffer.from(response.data, 'binary').toString('base64');
                setAvatar(`data:${response.headers['content-type'].toLowerCase()};base64,${buffer}`);
            }).catch(() => {
                getUIAvatar(name, size);
            });
        } else {
            getUIAvatar(name, size);
        }
    }, [gravatar, name, size]);

    const getUIAvatar = (name, size) => {
        axios.get('https://ui-avatars.com/api/', {
            params: {
                size: size,
                bold: 'true',
                name: name
            },
            responseType: 'arraybuffer'
        }).then((response) => {
            const buffer = Buffer.from(response.data, 'binary').toString('base64');
            setAvatar(`data:${response.headers['content-type'].toLowerCase()};base64,${buffer}`);
        });
    };

    return (
        <img className={className ? className : "rounded-circle" + (border ? " border border-1" : "")} width={size} height={size} src={avatar} alt={ name } />
    )
}

UserAvatar.defaultProps = {
    size: 50,
    border: false
};
