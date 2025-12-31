import apiClient from "./client";

export interface LLMProviderInfo {
  api_url: string;
  default_model: string;
  available_models: string[];
  api_key_configured: boolean;
}

export interface LLMConfig {
  active_provider: string;
  providers: Record<string, LLMProviderInfo>;
}

export interface LLMConfigUpdateRequest {
  active_provider?: string;
  provider_config?: Record<string, {
    api_key?: string;
    default_model?: string;
  }>;
}

export const llmApi = {
  get: async (): Promise<LLMConfig> => {
    const response = await apiClient.get("/config/llm");
    return response.data;
  },

  update: async (request: LLMConfigUpdateRequest): Promise<LLMConfig> => {
    const response = await apiClient.put("/config/llm", request);
    return response.data;
  },
};

