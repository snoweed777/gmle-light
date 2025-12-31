/**
 * Configuration field descriptions and recommended values
 */

export interface FieldDescription {
  label?: string;
  description: string;
  recommended?: unknown;
}

export const paramsDescriptions: Record<string, FieldDescription> = {
  total: {
    description: "1日に学習するカードの総数",
    recommended: 30,
  },
  new_total: {
    description: "1日に追加する新規カードの数",
    recommended: 10,
  },
  maintain_total: {
    description: "1日に復習する既存カードの数",
    recommended: 20,
  },
  coverage: {
    description: "各ドメインからの最低カード数",
    recommended: 3,
  },
  improve: {
    description: "改善が必要なカードの数",
    recommended: 7,
  },
  reward_cap: {
    description: "報酬の上限",
    recommended: 3,
  },
  domain_cap_steps: {
    description: "ドメインごとのカード数の上限ステップ",
    recommended: [6, 7, 8, 9999],
  },
  excerpt_min: {
    description: "抽出テキストの最小文字数",
    recommended: 200,
  },
  excerpt_max: {
    description: "抽出テキストの最大文字数",
    recommended: 800,
  },
  rationale_quote_max: {
    description: "解説の引用の最大文字数",
    recommended: 100,
  },
};

export const apiDescriptions: Record<string, Record<string, FieldDescription>> = {
  readwise: {
    api_url: {
      description: "Readwise API のエンドポイントURL",
      recommended: "https://readwise.io/api/v2/highlights/",
    },
  },
  anki: {
    connect_url: {
      description: "AnkiConnect のURL（ローカルホスト）",
      recommended: "http://127.0.0.1:8765",
    },
    connect_version: {
      description: "AnkiConnect のAPIバージョン",
      recommended: 6,
    },
    auto_sync: {
      description: "Anki の自動同期を有効化",
      recommended: true,
    },
    ankiweb: {
      username: {
        description: "AnkiWebユーザー名（環境変数ANKIWEB_USERNAMEで上書き可能）",
      },
      password: {
        description: "AnkiWebパスワード（暗号化されて保存されます）",
      },
      auto_login: {
        description: "Anki起動時に自動ログイン",
        recommended: true,
      },
    },
    headless: {
      enabled: {
        description: "ヘッドレスモード（GUI無し）を有効化",
        recommended: false,
      },
      xvfb_display: {
        description: "仮想ディスプレイ番号",
        recommended: ":99",
      },
      xvfb_screen_size: {
        description: "仮想ディスプレイの解像度",
        recommended: "1024x768x16",
      },
    },
  },
  generation: {
    microservice: {
      enabled: {
        description: "生成処理をマイクロサービス化",
        recommended: false,
      },
      url: {
        description: "生成マイクロサービスのURL",
        recommended: "http://localhost:8001",
      },
    },
  },
  ingest: {
    microservice: {
      enabled: {
        description: "取り込み処理をマイクロサービス化",
        recommended: false,
      },
      url: {
        description: "取り込みマイクロサービスのURL",
        recommended: "http://localhost:8002",
      },
    },
  },
};

export const loggingDescriptions: Record<string, FieldDescription> = {
  format: {
    description: "ログの出力形式（human: 人間が読みやすい形式、json: JSON形式）",
    recommended: "human",
  },
  level: {
    description: "ログレベル（DEBUG: 詳細、INFO: 通常、WARNING: 警告のみ、ERROR: エラーのみ）",
    recommended: "INFO",
  },
  file: {
    description: "ログファイルのパス（null: 自動設定）",
    recommended: null,
  },
  rotation_days: {
    description: "ログファイルのローテーション期間（日数）",
    recommended: 30,
  },
};

export const httpDescriptions: Record<string, FieldDescription> = {
  timeout: {
    description: "HTTPリクエストのタイムアウト時間（秒）",
    recommended: 30.0,
  },
  max_retries: {
    description: "HTTPリクエストの最大リトライ回数",
    recommended: 3,
  },
  retry_backoff_base: {
    description: "リトライ時のバックオフ基数（指数バックオフ）",
    recommended: 2,
  },
};

export const llmDescriptions: Record<string, FieldDescription> = {
  api_url: {
    description: "LLM API のエンドポイントURL",
  },
  default_model: {
    description: "使用するデフォルトのモデル",
  },
  api_key: {
    description: "API認証キー（暗号化されて保存されます）",
  },
};

export const promptDescriptions: Record<string, FieldDescription> = {
  stage1_extract: {
    label: "Stage 1: 事実抽出プロンプト",
    description: "ソーステキストから重要な事実を抽出するためのプロンプトテンプレート。利用可能な変数: {excerpt}",
  },
  stage2_build_mcq: {
    label: "Stage 2: MCQ生成プロンプト",
    description: "抽出された事実から多肢選択問題を生成するためのプロンプトテンプレート。利用可能な変数: {facts}",
  },
};

/**
 * Get nested description for API settings
 */
export function getApiDescription(
  category: string,
  field: string,
  subField?: string
): FieldDescription | undefined {
  const categoryDesc = apiDescriptions[category];
  if (!categoryDesc) return undefined;

  if (subField) {
    const fieldDesc = categoryDesc[field] as Record<string, FieldDescription>;
    return fieldDesc?.[subField];
  }

  return categoryDesc[field];
}

