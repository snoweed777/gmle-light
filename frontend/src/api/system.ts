import { apiClient } from "./client";

export interface ServiceStatus {
  name: string;
  status: "running" | "stopped" | "warning" | "error";
  pid?: number;
  port?: number;
  health_check?: string;
  warning?: string;
  error?: string;
  message?: string;
}

export interface SystemStatusResponse {
  services: Record<string, ServiceStatus>;
}

export const systemApi = {
  getStatus: async (): Promise<SystemStatusResponse> => {
    const response = await apiClient.get<SystemStatusResponse>("/system/status");
    return response.data;
  },

  getServiceStatus: async (serviceName: string): Promise<ServiceStatus> => {
    const response = await apiClient.get<ServiceStatus>(
      `/system/services/${serviceName}/status`
    );
    return response.data;
  },

  startService: async (serviceName: string): Promise<ServiceStatus> => {
    const response = await apiClient.post<ServiceStatus>(
      `/system/services/${serviceName}/start`
    );
    return response.data;
  },

  stopService: async (serviceName: string): Promise<ServiceStatus> => {
    const response = await apiClient.post<ServiceStatus>(
      `/system/services/${serviceName}/stop`
    );
    return response.data;
  },

  restartService: async (serviceName: string): Promise<ServiceStatus> => {
    const response = await apiClient.post<ServiceStatus>(
      `/system/services/${serviceName}/restart`
    );
    return response.data;
  },

  getRateLimitStatus: async (): Promise<RateLimitStatus> => {
    const response = await apiClient.get<RateLimitStatus>("/system/rate-limit");
    return response.data;
  },

  getHealthCheck: async (): Promise<HealthCheckReport> => {
    const response = await apiClient.get<HealthCheckReport>("/system/health");
    return response.data;
  },

  getApiKeyStatus: async (): Promise<ApiKeyStatus> => {
    const response = await apiClient.get<ApiKeyStatus>("/system/api-keys/status");
    return response.data;
  },
};

export interface RateLimitStatus {
  minute_tokens: number;
  hour_tokens: number;
  requests_per_minute: number;
  requests_per_hour: number;
  hour_request_count: number;
  next_minute_refill_seconds: number;
  next_hour_refill_seconds: number;
}

export interface HealthCheckIssue {
  severity: "error" | "warning" | "info";
  category: "dependency" | "path" | "config" | "permission";
  message: string;
  suggestion: string;
}

export interface HealthCheckReport {
  healthy: boolean;
  python_version: string;
  project_root: string;
  config_dir: string;
  spaces_dir: string;
  issues: HealthCheckIssue[];
  summary: {
    total: number;
    errors: number;
    warnings: number;
    infos: number;
  };
}

export interface ApiKeyStatus {
  valid: boolean;
  error?: string;
  key_type?: string;
  has_quota: boolean;
  error_detail?: string;
}

