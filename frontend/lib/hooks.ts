import { useEffect, useState } from "react";
import { getDarkMode, setDarkMode } from "./darkSide";
import { isNone } from "./utils";

export function useDarkMode() {
    const [isDark, _setIsDark] = useState(false);

    useEffect(() => {
        const tDark = getDarkMode();
        if (!isNone(tDark)) _setIsDark(tDark);
    }, []);

    // handler for changing/set dark mode
    const setIsDark = (dark: boolean) => {
        setDarkMode(dark);
        _setIsDark(dark);
    };
    return [isDark, setIsDark] as const;
}
