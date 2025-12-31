import apiClient from "./client";

export interface GlobalConfig {
  params: Record<string, unknown>;
  api: Record<string, unknown>;
  logging: Record<string, unknown>;
  http: Record<string, unknown>;
  rate_limit: Record<string, unknown>;
}

export interface GlobalConfigUpdateRequest {
  params?: Record<string, unknown>;
  api?: Record<string, unknown>;
  logging?: Record<string, unknown>;
  http?: Record<string, unknown>;
  rate_limit?: Record<string, unknown>;
}

export const globalApi = {
  get: async (): Promise<GlobalConfig> => {
    const response = await apiClient.get("/config/global");
    return response.data;
  },

  update: async (request: GlobalConfigUpdateRequest): Promise<GlobalConfig> => {
    const response = await apiClient.put("/config/global", request);
    return response.data;
  },
};

