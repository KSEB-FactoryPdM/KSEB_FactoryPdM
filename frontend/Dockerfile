# Next.js 프론트엔드 Dockerfile
FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치 (빌드를 위해 dev dependencies도 포함)
RUN npm ci

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 3000

# 환경 변수 설정
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# 개발 모드로 실행
CMD ["npm", "run", "dev"]
