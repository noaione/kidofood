export type NoneType = null | undefined;
export type Nullable<T> = T | NoneType;

export interface ResponseType<T> {
    data: T | null;
    error: string;
    code: number;
}
