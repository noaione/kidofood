const colors = require("tailwindcss/colors");

/**
 * @type {import("tailwindcss").Config}
 */
const Config = {
    content: [
        "./components/**/*.{js,ts,jsx,tsx}",
        "./lib/**/*.{js,ts,jsx,tsx}",
        "./models/**/*.{js,ts,jsx,tsx}",
        "./pages/**/*.{js,ts,jsx,tsx}",
        "./public/**/*.{js,ts,jsx,tsx,html,css}",
        "./states/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                gray: colors.neutral,
            },
        },
    },
};
module.exports = Config;
