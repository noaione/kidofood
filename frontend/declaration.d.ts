declare global {
    namespace NodeJS {
        // Extend process.env typing
        interface ProcessEnv {
            VERCEL_GIT_COMMIT_SHA?: string;
            NEXT_PUBLIC_BACKEND_API: string;
        }
    }
}

export {};
