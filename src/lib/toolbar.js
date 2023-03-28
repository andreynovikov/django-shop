import { useState, useEffect, createContext, useContext } from 'react';

export const ToolbarContext = createContext(null);

export function useToolbar(props) {
    const { item, setItem } = useContext(ToolbarContext);
    useEffect(() => {
        if (props === undefined)
            return;
        setItem(props);
        return () => setItem(null);
    }, [props, setItem]);
    return { item };
}

export function ToolbarProvider({children}) {
    const [item, setItem] = useState(null);

    return (
        <ToolbarContext.Provider value={{item, setItem}}>{children}</ToolbarContext.Provider>
    )
}
