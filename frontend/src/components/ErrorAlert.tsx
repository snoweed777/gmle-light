import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, RefreshCw } from "lucide-react";
import { ApiError, getErrorMessage, isRetryableError } from "@/api/errors";

interface ErrorAlertProps {
  title?: string;
  message?: string;
  error?: ApiError | Error | unknown;
  onRetry?: () => void;
}

export default function ErrorAlert({ title, message, error, onRetry }: ErrorAlertProps) {
  // Extract error information
  let errorMessage: string;
  let errorCode: string | undefined;
  let retryable = false;

  if (error) {
    if ("apiError" in error && error.apiError) {
      // Structured API error
      const apiError = error.apiError as ApiError;
      errorMessage = message || getErrorMessage(apiError);
      errorCode = apiError.code;
      retryable = isRetryableError(apiError);
    } else if ("error" in error && "code" in error) {
      // ApiError object
      const apiError = error as ApiError;
      errorMessage = message || getErrorMessage(apiError);
      errorCode = apiError.code;
      retryable = isRetryableError(apiError);
    } else if (error instanceof Error) {
      // Standard Error object
      errorMessage = message || error.message || "エラーが発生しました";
      errorCode = undefined;
      retryable = false;
    } else {
      // Unknown error type
      errorMessage = message || String(error) || "予期しないエラーが発生しました";
      errorCode = undefined;
      retryable = false;
    }
  } else {
    errorMessage = message || "エラーが発生しました";
    errorCode = undefined;
    retryable = false;
  }

  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      {title && <AlertTitle>{title}</AlertTitle>}
      <AlertDescription className="space-y-2">
        <div>{errorMessage}</div>
        {errorCode && (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {errorCode}
            </Badge>
            {retryable && (
              <Badge variant="secondary" className="text-xs">
                再試行可能
              </Badge>
            )}
          </div>
        )}
        {retryable && onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1 text-sm text-primary hover:underline mt-2"
          >
            <RefreshCw className="h-3 w-3" />
            再試行
          </button>
        )}
      </AlertDescription>
    </Alert>
  );
}

