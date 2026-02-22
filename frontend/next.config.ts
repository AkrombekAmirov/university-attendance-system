// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    output: "standalone",
    allowedDevOrigins: [
        "davomat.uznpu.uz",
        "api.davomat.uznpu.uz",
        "192.186.0.1",
        "localhost",
        "127.0.0.1",
    ],
};

export default nextConfig;
