import React from "react";
import { Provider } from "react-redux";

import { store } from "%/index";

import "../styles/global.css";
import type { AppProps } from "next/app";

function MyApp({ Component, pageProps }: AppProps) {
    return (
        <Provider store={store}>
            <Component {...pageProps} />;
        </Provider>
    );
}

export default MyApp;
