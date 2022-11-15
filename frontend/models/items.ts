import { Nullable } from "@/type";
import { AvatarResponse, ItemType } from "./common";

export interface FoodItem {
    id: string;
    name: string;
    description: string;
    price: number;
    stock: number;
    type: ItemType;
    image: Nullable<AvatarResponse>;

    // Timestamps (ISO 8601)
    created_at: string;
    updated_at: string;
}
