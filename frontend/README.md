# GMLE+ Frontend

GMLE+管理画面のフロントエンドアプリケーションです。

## 技術スタック

- **React 18+** (TypeScript)
- **Vite** (ビルドツール)
- **Tailwind CSS** (スタイリング)
- **Shadcn UI** (コンポーネントライブラリ)
- **React Query** (データフェッチ・キャッシュ)
- **React Router** (ルーティング)
- **Zustand** (状態管理)
- **Axios** (HTTPクライアント)

## セットアップ

### 前提条件

- Node.js 18+ と npm/yarn/pnpm が必要です
- バックエンドAPIサーバー（REST API）が起動している必要があります（ポート8000）

### インストール

```bash
cd frontend
npm install
```

### 開発サーバーの起動

```bash
npm run dev
```

開発サーバーは `http://localhost:3001` で起動します。

### ビルド

```bash
npm run build
```

### プレビュー

```bash
npm run preview
```

## プロジェクト構造

```
frontend/
├── src/
│   ├── api/          # REST APIクライアント
│   ├── components/   # 再利用可能コンポーネント
│   │   ├── ui/       # Shadcn UIコンポーネント
│   │   └── Layout.tsx
│   ├── pages/        # ページコンポーネント
│   ├── hooks/        # カスタムフック（useRunPolling等）
│   ├── lib/          # ユーティリティ（formatDate等）
│   ├── App.tsx       # メインアプリコンポーネント
│   └── main.tsx      # エントリーポイント
├── public/           # 静的ファイル
└── package.json
```

## 主要機能

### 画面一覧

- **Spaces**: スペース一覧表示
- **Space Detail**: スペース詳細・初期化機能
- **Runs**: 実行履歴・新規実行・リアルタイム監視
- **Items**: 生成されたMCQの一覧・検索・フィルタリング・詳細表示
- **Config**: Space固有の設定（params）の編集・保存
- **LLM Config**: LLMプロバイダーの選択・APIキー管理・モデル選択
- **Prompt Editor**: Stage1/Stage2のプロンプトテンプレート編集
- **Global Config**: 全パラメータへの日本語説明文・推奨値表示・ネスト設定の完全編集
- **Ingest**: ファイルアップロード（D&D対応）、既存ファイル一覧表示、Ingest手動実行、Ingest履歴表示（JST時刻表示）
- **System**: サービス（AnkiConnect、REST API、GUI Server）の状態確認・起動・停止、自動リフレッシュ（5秒間隔）

詳細な機能仕様は [`docs/GUI_TEST_SPEC.md`](../docs/GUI_TEST_SPEC.md) を参照してください。

## 環境変数

`.env.local` ファイルを作成して以下を設定：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 開発

### コードフォーマット

```bash
npm run format
```

### リンター

```bash
npm run lint
```

### 型チェック

```bash
npm run type-check
```

## 時刻表示

すべての時刻はJST（日本標準時）で表示されます。UTC時刻は自動的にJSTに変換されます。

