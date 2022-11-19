import { UserType } from "#/common";
import { User } from "#/user";
import { GETFromAPI } from "@/api";
import { isNone } from "@/utils";
import { GetServerSidePropsContext } from "next";

/**
 * Safe guard for pages that require the server to be claimed in.
 * Call the function like this:
 * ```ts
 * export const getServerSideProps = withServerSideGuard(async (ctx) => {
 *  // ...
 * });
 */
export function withServerClaimedGuard<T>(func: (ctx: GetServerSidePropsContext) => Promise<T>) {
    return async (ctx: GetServerSidePropsContext) => {
        const result = await GETFromAPI<User>("/api/server/claim");
        if ("detail" in result) {
            return {
                redirect: {
                    destination: "/login",
                    permanent: false,
                },
            };
        }

        if (isNone(result.data)) {
            // not yet claimed
            return {
                redirect: {
                    destination: "/claim",
                    permanent: false,
                },
            };
        }
        return func(ctx);
    };
}

export interface UserGuardOptions {
    adminOnly?: boolean;
    merchantOnly?: boolean;
}

/**
 * Check if user logged in or not.
 */
export function withUserGuard<T>(
    func: (ctx: GetServerSidePropsContext) => Promise<T>,
    options?: UserGuardOptions
) {
    return async (ctx: GetServerSidePropsContext) => {
        const result = await GETFromAPI<User>("/api/user/me");
        if ("detail" in result) {
            return {
                redirect: {
                    destination: "/login",
                    permanent: false,
                },
            };
        }
        if (isNone(result.data)) {
            return {
                redirect: {
                    destination: "/login",
                    permanent: false,
                },
            };
        }
        if (options?.adminOnly && result.data.type !== UserType.ADMIN) {
            return {
                redirect: {
                    destination: "/",
                    permanent: false,
                },
            };
        }
        if (options?.merchantOnly && result.data.type !== UserType.MERCHANT) {
            return {
                redirect: {
                    destination: "/",
                    permanent: false,
                },
            };
        }
        return func(ctx);
    };
}

interface UserCheckGuard {
    redirectTo?: string;
}

/**
 * Safe guard for pages that require the server to be claimed in.
 * Call the function like this:
 * ```ts
 * export const getServerSideProps = withServerSideGuard(async (ctx) => {
 *  // ...
 * });
 */
export function withUserCheckGuard<T>(
    func: (ctx: GetServerSidePropsContext) => Promise<T>,
    options?: UserCheckGuard
) {
    return async (ctx: GetServerSidePropsContext) => {
        console.info("Checking user");
        const result = await GETFromAPI<User>("/api/user/me");
        if ("detail" in result) {
            return {
                redirect: {
                    destination: "/login",
                    permanent: false,
                },
            };
        }
        if (!isNone(result.data)) {
            return {
                redirect: {
                    destination: options?.redirectTo ?? "/",
                    permanent: false,
                },
            };
        }
        return func(ctx);
    };
}
