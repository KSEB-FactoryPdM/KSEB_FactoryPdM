import nextJest from 'next/jest'

const createJestConfig = nextJest({ dir: './' })

const customJestConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',            // "@/..." 별칭 매핑
  },
}

export default createJestConfig(customJestConfig)
