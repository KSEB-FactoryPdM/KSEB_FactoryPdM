// src/app/page.tsx
import { redirect } from "next/navigation";

export default function Page() {
  // 기본 대시보드 페이지로 이동
  redirect("/monitoring");
}
