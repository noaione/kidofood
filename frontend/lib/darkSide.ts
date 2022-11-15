import { Nullable, UndefinedOr } from "./type";
import { isDOMAvailable, isNone } from "./utils";

/**
 * The theme/dark mode key on localStorage.
 */
export const THEME_KEY = "kidofood.theme";

/**
 * Get the website dark mode status.
 * @returns true if dark mode is enabled
 */
export const getDarkMode = (): Nullable<boolean> => {
    if (!isDOMAvailable()) return null;

    let userPreferDark: UndefinedOr<boolean>;
    let systemPreferDark = false;
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        systemPreferDark = true;
    }

    try {
        const themeStorage = window.localStorage.getItem(THEME_KEY);
        if (!isNone(themeStorage)) {
            userPreferDark = themeStorage === "dark" ? true : false;
        }
    } catch (e) {}

    return userPreferDark ?? systemPreferDark;
};

/**
 * Set the website dark mode status.
 * @param target Whether to enable dark mode or not
 */
export const setDarkMode = (target: boolean) => {
    if (!isDOMAvailable()) return;
    const root = window.document.documentElement;
    if (target) {
        if (!root.classList.contains("dark")) {
            root.classList.add("dark");
        }
    } else {
        if (root.classList.contains("dark")) {
            root.classList.remove("dark");
        }
    }
    window.localStorage.setItem(THEME_KEY, target ? "dark" : "light");
};
