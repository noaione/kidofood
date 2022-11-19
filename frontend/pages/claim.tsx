import LoginLayout from "$/LoginLayout";
import { withServerClaimedGuard } from "@/guards";
import React from "react";

export const getServerSideProps = withServerClaimedGuard(async () => {
    return {
        props: {},
    };
});

export default function ClaimServerPage() {
    return (
        <LoginLayout withHeader={false}>
            <div className="text-center mt-5">
                <h1 className="font-bold text-3xl text-gray-900">Claim your server</h1>
                <p>
                    To be able to use{" "}
                    <span className="font-bold">
                        <span className="font-light">Kido</span>Food
                    </span>
                </p>
            </div>
        </LoginLayout>
    );
}
