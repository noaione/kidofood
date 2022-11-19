import { OrderStatus, PartialID, PartialIDAvatar } from "./common";
import { FoodItem } from "./items";

export interface FoodOrder extends PartialID {
    items: FoodItem[];
    total: number;

    user: PartialIDAvatar;
    merchant: PartialIDAvatar;

    target_address: string;
    status: OrderStatus;

    // Timestamps (ISO 8601)
    created_at: string;
    updated_at: string;
}
