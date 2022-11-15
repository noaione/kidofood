import React from "react";
import Image from "next/image";
import { useSelector } from "react-redux";

import CartIcon from "@heroicons/react/24/outline/ShoppingCartIcon";
import DarkIcon from "@heroicons/react/24/outline/MoonIcon";
import LightIcon from "@heroicons/react/24/solid/SunIcon";
import LoginIcon from "@heroicons/react/24/outline/ArrowRightOnRectangleIcon";
import UserIcon from "@heroicons/react/24/outline/UserIcon";
import SearchIcon from "@heroicons/react/20/solid/MagnifyingGlassIcon";

import LogoV1 from "~~/assets/img/logov1.png";
import { RootState } from "%/index";
import { useDarkMode } from "@/hooks";
import { isNone } from "@/utils";

export default function NavHeader() {
    const userState = useSelector((state: RootState) => state.user);
    const [isDark, setIsDark] = useDarkMode();

    // Header design:
    // LOGO / Text ==================== SEARCH? / CART / LIGHT SWITCH / ACCOUNT
    return (
        <header className="flex flex-row justify-between bg-gray-200 dark:bg-gray-600 shadow-lg dark:shadow-gray-700">
            <div className="flex flex-row gap-2 mx-4 my-4 items-center w-full">
                <div className="w-10 h-10">
                    <Image src={LogoV1} className="object-contain object-center" alt="Logo" />
                </div>
                <div className="hidden lg:block">
                    <h1 className="text-2xl font-bold">
                        <span className="font-light">Kido</span>Food
                    </h1>
                </div>
            </div>
            <div className="flex flex-row mx-4 my-4 gap-4 items-center justify-between w-full">
                <div className="hidden md:flex flex-row gap-2 items-center w-full">
                    {/* Icon */}
                    <div className="w-[1.1rem] h-[1.1rem] absolute ml-3 translate-y-[0.05rem]">
                        <SearchIcon className="w-full h-full" />
                    </div>
                    <input
                        type="text"
                        className="w-full py-2 pr-4 pl-10 rounded-md hover:rounded-xl focus:ring-0 focus:rounded-xl transition-all bg-gray-300 dark:bg-gray-800 outline-none focus:outline-2 focus:outline-purple-500"
                    />
                </div>
                <div className="flex flex-row gap-2 lg:gap-4 items-center">
                    <button
                        className="hover:opacity-80 transition-opacity"
                        onClick={() => setIsDark(!isDark)}
                    >
                        {isDark ? <LightIcon className="w-6 h-6" /> : <DarkIcon className="w-6 h-6" />}
                    </button>
                    <button className="hover:opacity-80 transition-opacity">
                        <CartIcon className="w-6 h-6" />
                    </button>
                    <button className="hover:opacity-80 transition-opacity">
                        {isNone(userState) ? (
                            <LoginIcon className="w-6 h-6" />
                        ) : (
                            <UserIcon className="w-6 h-6" />
                        )}
                    </button>
                </div>
            </div>
        </header>
    );
}
