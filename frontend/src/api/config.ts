import { apiClient } from "./client";

export interface ConfigResponse {
  space_id: string;
  params: Record<string, unknown>;
  paths: Record<string, string>;
}

export interface ConfigUpdateRequest {
  params?: Record<string, unknown>;
}

export const configApi = {
  get: async (spaceId: string): Promise<ConfigResponse> => {
    const response = await apiClient.get<ConfigResponse>(
      `/spaces/${spaceId}/config`
    );
    return response.data;
  },

  update: async (
    spaceId: string,
    request: ConfigUpdateRequest
  ): Promise<ConfigResponse> => {
    const response = await apiClient.put<ConfigResponse>(
      `/spaces/${spaceId}/config`,
      request
    );
    return response.data;
  },
};

