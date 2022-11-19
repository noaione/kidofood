import { PartialIDAvatar } from "./common";

export type MerchantSearch = PartialIDAvatar;

export interface FoodItemSearch extends PartialIDAvatar {
    description: string;
    price: number;
}

export interface MultiSearch {
    merchants: MerchantSearch[];
    items: FoodItemSearch[];
}
