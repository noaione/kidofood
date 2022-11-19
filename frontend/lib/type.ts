export type NoneType = null | undefined;
export type Nullable<T> = T | null;
export type UndefinedOr<T> = T | NoneType;

export interface ResponseType<T> {
    data: Nullable<T>;
    error: string;
    code: number;
}

export interface DefaultErrorResponse {
    detail: string;
}
