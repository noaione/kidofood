import { UserType } from "./common";

export interface LoginRequest {
    email: string;
    password: string;
    remember?: boolean;
}

export interface RegisterRequest {
    email: string;
    password: string;
    name: string;
}

export interface User {
    user_id: string;
    email: string;
    name: string;
    type: UserType;
}
