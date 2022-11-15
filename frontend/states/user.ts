import { User } from "#/user";
import { Nullable } from "@/type";
import { createModel } from "@rematch/core";
import type { RootModel } from "./model";

export const userReducer = createModel<RootModel>()({
    state: null as Nullable<User>,
    reducers: {
        setSession(_, payload: User) {
            return payload;
        },
        delSession(_) {
            return null;
        },
    },
});
