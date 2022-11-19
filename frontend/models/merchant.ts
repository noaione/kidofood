import { Nullable, ResponseType } from "@/type";
import { PartialIDAvatar } from "./common";

export interface Merchant extends PartialIDAvatar {
    description: string;
    address: string;

    // Optional stuff
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
