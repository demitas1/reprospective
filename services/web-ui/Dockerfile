# Web UIコンテナ（Vite Dev Server）
# 実験プロジェクトのため本番環境でもViteの開発サーバーを使用

FROM node:20-alpine

WORKDIR /app

# 依存パッケージのインストール
COPY package.json package-lock.json ./
RUN npm ci

# ソースコードのコピー
COPY . .

# Viteの開発サーバーポートを公開
EXPOSE 5173

# 開発サーバーを起動（--host 0.0.0.0でコンテナ外からのアクセスを許可）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
