import type { NoneType } from "./type";

export const isDOMAvailable = () => {
    return typeof window !== "undefined" && typeof window.document !== "undefined";
};

export function isNone(value: any): value is NoneType {
    return value === null || value === undefined;
}
