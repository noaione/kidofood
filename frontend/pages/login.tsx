import LoginLayout from "$/LoginLayout";
import { withServerClaimedGuard, withUserCheckGuard } from "@/guards";
import React from "react";

import EmailIcon from "@heroicons/react/24/outline/EnvelopeIcon";
import PasswordIcon from "@heroicons/react/24/outline/KeyIcon";
import Link from "next/link";

export const getServerSideProps = withUserCheckGuard(
    withServerClaimedGuard(async () => {
        return {
            props: {},
        };
    })
);

export default function LoginPage() {
    return (
        <LoginLayout withSearch={false}>
            <div className="flex flex-col justify-center text-center mt-5">
                <h1 className="font-bold text-3xl text-gray-900 dark:text-white mb-2">Login</h1>
                <p>
                    Welcome to{" "}
                    <span className="font-bold text-black dark:text-white glow-text">
                        <span className="font-light">Kido</span>Food
                    </span>{" "}
                    before you can purchase food, please login to our system first!
                </p>
            </div>
            <form
                onSubmit={(ev) => ev.preventDefault()}
                className="flex flex-col justify-center items-center w-full mt-6"
            >
                <div className="flex flex-col max-w-[90%] w-full mb-3">
                    <div className="flex w-full px-3 ">
                        <div className="w-10 z-10 pl-1 text-center pointer-events-none flex items-center justify-center">
                            <EmailIcon className="w-6 h-6" />
                        </div>
                        <input
                            className="w-full -ml-10 pl-10 pr-3 py-2 rounded-lg border-2 transition-colors duraion-400 ease-in-out border-gray-200 dark:border-gray-800 focus:dark:border-yellow-600 focus:border-yellow-600 focus:outline-none dark:bg-gray-800"
                            type="email"
                            name="email"
                            placeholder="user@kidofood.com"
                        />
                    </div>
                </div>
                <div className="flex flex-col max-w-[90%] w-full mb-4">
                    <div className="flex w-full px-3">
                        <div className="w-10 z-10 pl-1 text-center pointer-events-none flex items-center justify-center">
                            <PasswordIcon className="w-6 h-6" />
                        </div>
                        <input
                            className="w-full -ml-10 pl-10 pr-3 py-2 rounded-lg border-2 transition-colors duraion-400 ease-in-out border-gray-200 dark:border-gray-800 focus:dark:border-yellow-600 focus:border-yellow-600 focus:outline-none dark:bg-gray-800"
                            type="password"
                            name="password"
                            placeholder="********"
                        />
                    </div>
                </div>
                <div className="flex flex-col max-w-[90%] w-full">
                    <div className="flex w-full px-3">
                        <input
                            className="w-full bg-red-600 text-white rounded-lg font-bold hover:opacity-80 transition-opacity py-3"
                            type="submit"
                            name="password"
                            value="Login"
                        />
                    </div>
                </div>
            </form>
            <div className="flex flex-row justify-center mb-7 mt-4">
                <Link href="/register" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                    Register
                </Link>
            </div>
        </LoginLayout>
    );
}
