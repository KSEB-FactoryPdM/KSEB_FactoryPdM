// 인증이 필요한 API 호출을 처리하는 헬퍼 함수
export async function fetchWithAuth(input: RequestInfo, init: RequestInit = {}) {
  // 브라우저 환경에서만 로컬 스토리지를 확인
  if (typeof window !== 'undefined') {
    // 저장된 토큰이 있으면 요청 헤더에 추가
    const token = localStorage.getItem('token')
    if (token) {
      const headers = new Headers(init.headers || {})
      headers.set('Authorization', `Bearer ${token}`)
      init.headers = headers
    }
  }
  // 최종 fetch 호출 실행
  return fetch(input, init)
}
