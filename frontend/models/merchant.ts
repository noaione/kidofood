import { Nullable, ResponseType } from "@/type";
import { AvatarResponse } from "./common";

export interface Merchant {
    id: string;
    name: string;
    description: string;
    address: string;

    // Optional stuff
    avatar: Nullable<AvatarResponse>;
    phone: Nullable<string>;
    email: Nullable<string>;
    website: Nullable<string>;

    // Timestamps (ISO 8601)
    created_at: string;
    updated_at: string;
}

export type MerchantList = Merchant[];
export type MerchantResponse = ResponseType<Merchant>;
export type MerchantListResponse = ResponseType<MerchantList>;
