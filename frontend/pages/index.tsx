import Head from "next/head";
import React from "react";

import Image from "next/image";
import NavHeader from "$/NavHeader";

export default function Main() {
    return (
        <>
            <Head>
                <title>Welcome to noaione/nextjs-template bootstrap</title>
            </Head>
            <NavHeader />
            <main className="mx-auto">
                <div className="flex flex-col items-center mt-16">
                    <Image
                        src="https://cdn.discordapp.com/emojis/774990963310985226.gif"
                        alt="InaNod"
                        className="text-center align-middle"
                        width={100}
                        height={100}
                    />
                </div>
            </main>
        </>
    );
}
