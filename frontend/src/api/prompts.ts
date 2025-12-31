import apiClient from "./client";

export interface PromptInfo {
  description: string;
  template: string;
}

export interface PromptsConfig {
  stage1_extract: PromptInfo;
  stage2_build_mcq: PromptInfo;
}

export interface PromptsConfigUpdateRequest {
  stage1_extract?: {
    template?: string;
    description?: string;
  };
  stage2_build_mcq?: {
    template?: string;
    description?: string;
  };
}

export const promptsApi = {
  get: async (): Promise<PromptsConfig> => {
    const response = await apiClient.get("/config/prompts");
    return response.data;
  },

  update: async (request: PromptsConfigUpdateRequest): Promise<PromptsConfig> => {
    const response = await apiClient.put("/config/prompts", request);
    return response.data;
  },
};

