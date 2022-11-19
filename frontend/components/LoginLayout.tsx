import React from "react";
import NavHeader from "./NavHeader";

interface LayoutProps {
    withHeader?: boolean;
    withSearch?: boolean;
}

export default function LoginLayout(props: React.PropsWithChildren<LayoutProps>) {
    const { withHeader = true, withSearch = false, children } = props;
    return (
        <>
            {withHeader && <NavHeader withSearch={withSearch} />}
            <div className="flex justify-center px-0 md:px-5 py-5">
                <div className="bg-gray-300 text-gray-700 dark:bg-gray-600 dark:text-gray-200 rounded-none md:rounded-3xl shadow-xl w-full overflow-hidden">
                    <div className="flex flex-wrap flex-grow flex-col w-full">{children}</div>
                </div>
            </div>
        </>
    );
}
