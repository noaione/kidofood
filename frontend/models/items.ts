import { Nullable } from "@/type";
import { AvatarResponse, ItemType, PartialIDAvatar, PartialIDName } from "./common";

export interface FoodItem extends PartialIDName {
    description: string;
    price: number;
    stock: number;
    type: ItemType;
    merchant: PartialIDAvatar;
    image: Nullable<AvatarResponse>;

    // Timestamps (ISO 8601)
    created_at: string;
    updated_at: string;
}
