import { defineConfig } from 'cypress'

// Cypress 테스트 설정
export default defineConfig({
  e2e: {
    // 테스트 실행 기본 주소
    baseUrl: 'http://localhost:3000',
    // 공용 지원 파일 위치
    supportFile: 'cypress/support/e2e.ts',
  },
})
