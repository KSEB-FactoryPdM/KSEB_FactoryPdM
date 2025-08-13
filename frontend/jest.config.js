const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  // 차트/ESM 라이브러리 때문에 필요해질 수 있음 — 문제 생기면 주석 해제
  // transformIgnorePatterns: [
  //   '/node_modules/(?!(@?react-.*|d3|d3-.*|chart\\.js|echarts|recharts)/)',
  // ],
}

module.exports = createJestConfig(customConfig)
