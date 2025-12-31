import { apiClient } from "./client";

export interface ItemResponse {
  id: string;
  source_id: string;
  domain_path: string;
  format: string;
  depth: number;
  question: string;
  choices: string[];
  answer: string;
  rationale: {
    quote: string;
    explain: string;
  };
  source: {
    title: string;
    locator: string;
    url?: string;
  };
  meta: Record<string, unknown>;
  retired: boolean;
}

export const itemsApi = {
  list: async (
    spaceId: string,
    retired?: boolean
  ): Promise<ItemResponse[]> => {
    const params = retired !== undefined ? { retired: retired.toString() } : {};
    const response = await apiClient.get<ItemResponse[]>(
      `/spaces/${spaceId}/items`,
      { params }
    );
    return response.data;
  },

  get: async (spaceId: string, itemId: string): Promise<ItemResponse> => {
    const response = await apiClient.get<ItemResponse>(
      `/spaces/${spaceId}/items/${itemId}`
    );
    return response.data;
  },
};

