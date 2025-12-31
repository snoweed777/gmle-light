# GMLE Light

**Lightweight MCQ Generator with Local Anki Integration**

GMLE Lightは、LLMを使用して学習教材から多肢選択問題（MCQ）を自動生成し、ローカルのAnkiに注入するツールです。

## 特徴

- 🚀 **軽量**: Docker内にAnkiを含まず、シンプルな構成
- 🔗 **ローカルAnki連携**: Mac上のAnki + AnkiConnectと直接通信
- 🤖 **LLM統合**: Cohere / Gemini / Groq対応
- 🌐 **Web GUI**: React + Vite による管理画面
- 📡 **REST API**: FastAPI による API

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Container                    Mac Local               │
│ ┌────────────┐                     ┌──────────────────────┐│
│ │ REST API   │ ───HTTP:8765────→   │ Anki + AnkiConnect  ││
│ │ :8000      │                     │         ↓           ││
│ ├────────────┤                     │    AnkiWeb Sync     ││
│ │ GUI        │                     └──────────────────────┘│
│ │ :3001      │                                              │
│ └────────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

## 前提条件

### Mac側の準備

1. **Anki** をインストール
   - https://apps.ankiweb.net/ からダウンロード

2. **AnkiConnect** アドオンをインストール
   - Anki → ツール → アドオン → アドオンを取得
   - コード: `2055492159`

3. **Ankiを起動**しておく（バックグラウンドでOK）

### 環境変数

`.env.example` を `.env` にコピーして、APIキーを設定：

```bash
cp .env.example .env
```

```env
# LLM API Keys (少なくとも1つ必要)
COHERE_API_KEY=your_cohere_api_key
GROQ_API_KEY=your_groq_api_key
GOOGLE_AI_API_KEY=your_google_ai_api_key

# Optional
READWISE_TOKEN=your_readwise_token
```

## クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/snoweed777/gmle-light.git
cd gmle-light

# 2. 環境変数を設定
cp .env.example .env
# .env を編集してAPIキーを設定

# 3. Anki（with AnkiConnect）を起動（Mac側）

# 4. Docker起動
docker-compose up -d

# 5. ブラウザでGUIを開く
open http://localhost:3001
```

## 使い方

### GUI

1. http://localhost:3001 にアクセス
2. **Spaces** でスペースを選択/作成
3. **Ingest** でテキストファイルをアップロード
4. **Runs** でMCQ生成を実行
5. 生成されたMCQはローカルAnkiに自動追加

### CLI

```bash
# コンテナに入る
docker-compose exec gmle-light bash

# スペース一覧
gmle list-spaces

# MCQ生成実行
gmle run --space cissp

# Anki接続確認
gmle selfcheck --space cissp
```

## 設定

### config/gmle.yaml

主要な設定：

```yaml
api:
  anki:
    # Docker内からホストMacのAnkiConnectに接続
    connect_url: http://host.docker.internal:8765
    connect_version: 6

llm:
  active_provider: groq  # cohere / gemini / groq
```

## トラブルシューティング

### AnkiConnectに接続できない

1. Mac側でAnkiが起動しているか確認
2. AnkiConnectがインストールされているか確認
3. ターミナルで接続テスト:
   ```bash
   curl -X POST http://localhost:8765 \
     -H "Content-Type: application/json" \
     -d '{"action":"version","version":6}'
   ```

### Dockerコンテナからホストに接続できない

`docker-compose.yml` に以下が設定されていることを確認：
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

## ライセンス

MIT License

## 関連プロジェクト

- [GMLE+](https://github.com/snoweed777/gmle-plus) - Docker内Anki統合版（フル機能）
- [AnkiConnect](https://foosoft.net/projects/anki-connect/) - Anki APIアドオン

