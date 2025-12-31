import axios, { AxiosError } from "axios";
import { extractApiError, ApiError } from "./errors";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export { apiClient };
export default apiClient;

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Extract structured error information
    const apiError = extractApiError(error);
    
    // Attach structured error to error object for easier access
    (error as any).apiError = apiError;
    
    // Log error with structured information
    if (error.response) {
      console.error("API Error:", {
        code: apiError.code,
        message: apiError.error,
        status: error.response.status,
        details: apiError.details,
        retryable: apiError.retryable,
      });
    } else if (error.request) {
      console.error("Network Error:", {
        code: apiError.code,
        message: apiError.error,
      });
    } else {
      console.error("Error:", {
        code: apiError.code,
        message: apiError.error,
      });
    }
    
    return Promise.reject(error);
  }
);

// Type augmentation for axios errors
declare module "axios" {
  export interface AxiosError {
    apiError?: ApiError;
  }
}

