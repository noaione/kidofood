import axios, { AxiosError } from "axios";
import { DefaultErrorResponse, ResponseType } from "./type";
import { isNone } from "./utils";

function getBackendAPI() {
    const { NEXT_PUBLIC_BACKEND_API } = process.env;
    if (!NEXT_PUBLIC_BACKEND_API) {
        throw new Error("NEXT_PUBLIC_BACKEND_API is not set");
    }
    return NEXT_PUBLIC_BACKEND_API.endsWith("/")
        ? NEXT_PUBLIC_BACKEND_API.slice(0, -1)
        : NEXT_PUBLIC_BACKEND_API;
}

export const BACKEND_API = getBackendAPI();

const api = axios.create({
    baseURL: BACKEND_API,
});

type Responses<T> = ResponseType<T> | DefaultErrorResponse;

export async function GETFromAPI<T = any>(url: string): Promise<Responses<T>> {
    try {
        const { data } = await api.get(url);
        return data as ResponseType<T>;
    } catch (error) {
        const errorAct = error as AxiosError<Responses<T>>;
        const { response } = errorAct;
        if (isNone(response)) {
            return {
                detail: "Unknown error",
            };
        }
        const { data } = response;
        return data;
    }
}
