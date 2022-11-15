/**
 * @type {import("next").NextConfig}
 */
const nextConfig = {
    productionBrowserSourceMaps: true,
    swcMinify: true,
    reactStrictMode: true,
    headers: async () => {
        return [
            {
                source: "/:path*",
                headers: [
                    {
                        key: "Permissions-Policy",
                        value: "interest-cohort=()",
                    },
                ],
            },
        ];
    },
    images: {
        domains: ["s3.ap-southeast-1.wasabisys.com", "cdn.discordapp.com", "cdn.discord.com"],
    },
};
module.exports = nextConfig;
