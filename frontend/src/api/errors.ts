/**
 * Structured error handling for API responses.
 */

export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, any>;
  retryable?: boolean;
}

export interface ApiErrorResponse {
  data?: ApiError;
  status?: number;
  statusText?: string;
}

/**
 * Extract structured error information from axios error.
 */
export function extractApiError(error: any): ApiError {
  // Check if error has structured API error response
  if (error?.response?.data) {
    const data = error.response.data;
    if (data.error && data.code) {
      return {
        error: data.error,
        code: data.code,
        details: data.details || {},
        retryable: data.retryable ?? false,
      };
    }
  }

  // Fallback to generic error
  if (error.response) {
    return {
      error: error.response.data?.message || error.response.statusText || "サーバーエラーが発生しました",
      code: `HTTP_${error.response.status}`,
      details: { status: error.response.status },
      retryable: error.response.status >= 500,
    };
  }

  if (error.request) {
    return {
      error: "ネットワークエラーが発生しました。接続を確認してください。",
      code: "NETWORK_ERROR",
      details: {},
      retryable: true,
    };
  }

  return {
    error: error.message || "予期しないエラーが発生しました",
    code: "UNKNOWN_ERROR",
    details: {},
    retryable: false,
  };
}

/**
 * Get user-friendly error message based on error code.
 */
export function getErrorMessage(error: ApiError): string {
  const codeMessages: Record<string, string> = {
    AUTH_ERROR: "認証エラーが発生しました。APIキーを確認してください。",
    RATE_LIMIT: "レート制限に達しました。しばらく待ってから再試行してください。",
    MONTHLY_LIMIT: "月次API制限に達しました。",
    SERVER_ERROR: "サーバーエラーが発生しました。しばらく待ってから再試行してください。",
    REQUEST_ERROR: "リクエストが失敗しました。ネットワーク接続を確認してください。",
    ANKI_ERROR: "Ankiサービスエラーが発生しました。AnkiConnectが起動しているか確認してください。",
    CONFIG_ERROR: "設定エラーが発生しました。設定を確認してください。",
    INFRA_ERROR: "インフラエラーが発生しました。",
    SOT_ERROR: "データエラーが発生しました。",
    DEGRADE_TRIGGER: "Degradeモードがトリガーされました。",
    NETWORK_ERROR: "ネットワークエラーが発生しました。接続を確認してください。",
  };

  return codeMessages[error.code] || error.error;
}

/**
 * Check if error is retryable.
 */
export function isRetryableError(error: ApiError): boolean {
  return error.retryable ?? false;
}

