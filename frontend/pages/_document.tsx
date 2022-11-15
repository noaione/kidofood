import React from "react";
import Document, { DocumentContext, Head, Html, Main, NextScript } from "next/document";

import { InlineJs } from "@kachkaev/react-inline-js";

const THEME_CHECKER_JS = `
// Helper
const STORAGE_KEY = "kidofood.theme";
const isNullified = function(data) {
    return typeof data === "undefined" || data === null;
}

// Check for first user preferences.
let userPreferDark;
let systemPreferDark = false;
if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    systemPreferDark = true;
}
try {
    const themeStorage = localStorage.getItem(STORAGE_KEY);
    if (!isNullified(themeStorage)) {
        userPreferDark = themeStorage === "dark" ? true : false;
    }
} catch (e) {};
if (isNullified(userPreferDark)) {
    if (systemPreferDark) {
        document.documentElement.classList.add("dark");
        localStorage.setItem(STORAGE_KEY, "dark");
    } else {
        localStorage.setItem(STORAGE_KEY, "light");
    }
} else {
    if (userPreferDark) {
        document.documentElement.classList.add("dark");
    }
}
`;

class MyDocument extends Document {
    static async getInitialProps(ctx: DocumentContext) {
        const initialProps = await Document.getInitialProps(ctx);
        return { ...initialProps };
    }

    render() {
        return (
            <Html>
                <Head>
                    <InlineJs code={THEME_CHECKER_JS} />
                </Head>
                <body className="bg-white dark:bg-gray-800 text-black dark:text-white transition-colors">
                    <Main />
                    <NextScript />
                </body>
            </Html>
        );
    }
}

export default MyDocument;
