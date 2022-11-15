export enum ItemType {
    DRINK = "drink",
    MEAL = "meal",
    PACKAGE = "package",
}

export enum UserType {
    CUSTOMER = 0,
    MERCHANT = 1,
    ADMIN = 999,
}

export enum OrderStatus {
    /**
     * Pending payment
     */
    PENDING = 0,
    /**
     * Payment is done, submitted to merchant
     */
    FORWARDED = 1,
    /**
     * Merchant accepted the order, processing
     */
    ACCEPTED = 2,
    /**
     * Merchant processing the order
     */
    PROCESSING = 3,
    /**
     * Merchant finished processing the order, delivery
     * in progress
     */
    DELIVERING = 4,
    /**
     * Merchant rejected the order
     */
    REJECTED = 100,
    /**
     * User cancelled the order
     */
    CANCELLED = 101,
    /**
     * Merchant canceled the order
     */
    CANCELED_MERCHANT = 102,
    /**
     * Problem with the order from the merchant side
     */
    PROBLEM_MERCHANT = 103,
    /**
     * Problem with delivery
     */
    PROBLEM_FAIL_TO_DELIVER = 104,
    /**
     * Order is completed
     */
    DONE = 200,
}

export interface AvatarResponse {
    name: string;
    type: string;
}
