import { Models } from "@rematch/core";
import { userReducer } from "./user";

// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface RootModel extends Models<RootModel> {
    user: typeof userReducer;
}
export const models: RootModel = { user: userReducer };
