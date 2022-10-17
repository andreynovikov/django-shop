import { useEffect } from 'react';
import { useSession } from 'next-auth/react';

const RefreshTokenHandler = (props) => {
    const { data: session } = useSession();

    useEffect(() => {
        if(!!session) {
            const timeRemaining = (session.accessTokenExpires - Date.now()) / 1000;
            props.setInterval(timeRemaining > 0 ? timeRemaining : 0);
        }
    }, [session]);

    return null;
}

export default RefreshTokenHandler;
