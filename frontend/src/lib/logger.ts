// 일반 로그 출력 함수
export const info = (...args: unknown[]) => {
  console.log(...args)
}

// 개발 모드에서만 디버그 로그를 출력
export const debug = (...args: unknown[]) => {
  if (process.env.NODE_ENV !== 'production') {
    console.debug(...args)
  }
}

// 에러 로그 출력 함수
export const error = (...args: unknown[]) => {
  console.error(...args)
}
