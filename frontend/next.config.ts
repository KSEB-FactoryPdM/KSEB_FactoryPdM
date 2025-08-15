import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 엄격 모드 활성화
  reactStrictMode: true,
  // 실험 기능: typedRoutes
  experimental: {
    typedRoutes: true,
  },
  // i18n 설정 제거 (App Router에서 지원되지 않음)
};

export default nextConfig;
