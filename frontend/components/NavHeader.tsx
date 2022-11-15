import React from "react";
import Image from "next/image";
import { useSelector } from "react-redux";

import CartIcon from "@heroicons/react/24/outline/ShoppingCartIcon";
import DarkIcon from "@heroicons/react/24/outline/MoonIcon";
import LightIcon from "@heroicons/react/24/outline/SunIcon";
import LoginIcon from "@heroicons/react/24/outline/ArrowRightOnRectangleIcon";
import UserIcon from "@heroicons/react/24/outline/UserIcon";

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
            <div className="flex flex-row gap-2 mx-4 my-4 items-center">
                <div className="w-10 h-10">
                    <Image src={LogoV1} className="object-contain object-center" alt="Logo" />
                </div>
                <div className="hidden lg:block">
                    <h1 className="text-2xl font-bold">
                        <span className="font-light">Kido</span>Food
                    </h1>
                </div>
            </div>
            <div className="flex flex-row gap-2 mx-4 my-4 items-center">
                <button className="hover:opacity-80 transition-opacity" onClick={() => setIsDark(!isDark)}>
                    {isDark ? <LightIcon className="w-6 h-6" /> : <DarkIcon className="w-6 h-6" />}
                </button>
                <button className="hover:opacity-80 transition-opacity">
                    <CartIcon className="w-6 h-6" />
                </button>
                <button className="hover:opacity-80 transition-opacity">
                    {isNone(userState) ? <LoginIcon className="w-6 h-6" /> : <UserIcon className="w-6 h-6" />}
                </button>
            </div>
        </header>
    );
}
