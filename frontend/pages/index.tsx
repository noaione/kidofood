import Head from "next/head";
import React from "react";

export default function Main() {
    return (
        <>
            <Head>
                <title>Welcome to noaione/nextjs-template bootstrap</title>
            </Head>
            <main className="mx-auto">
                <div className="flex flex-col items-center mt-16">
                    <img
                        src="https://cdn.discordapp.com/emojis/774990963310985226.gif"
                        alt="InaNod"
                        className="text-center align-middle"
                    />
                </div>
                <h1 className="mt-6 text-3xl font-semibold text-center">Welcome!</h1>
                <p className="text-center mt-4">
                    You can start editing this page by editing{" "}
                    <code className="text-red-600 dark:text-red-400 bg-gray-100 rounded-sm px-0.5 dark:bg-gray-800">
                        pages/index.tsx
                    </code>
                </p>
                <p className="text-center">
                    You can also try to modify and configure this bootstrap project!
                </p>
            </main>
        </>
    );
}
