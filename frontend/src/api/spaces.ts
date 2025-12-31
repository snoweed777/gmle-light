import { apiClient } from "./client";

export interface SpaceInfo {
  space_id: string;
  deck_bank: string;
  data_root: string;
  sources_root: string;
}

export interface AnkiStatus {
  note_type_exists: boolean;
  deck_exists: boolean;
  note_type_name: string;
  deck_name: string;
}

export interface AnkiInitializeResponse {
  success: boolean;
  note_type_created: boolean;
  deck_created: boolean;
  message: string;
}

export interface CreateSpaceRequest {
  space_id: string;
  description?: string;
}

export const spacesApi = {
  list: async (): Promise<SpaceInfo[]> => {
    const response = await apiClient.get<SpaceInfo[]>("/spaces");
    return response.data;
  },

  create: async (request: CreateSpaceRequest): Promise<SpaceInfo> => {
    const response = await apiClient.post<SpaceInfo>("/spaces", request);
    return response.data;
  },

  get: async (spaceId: string): Promise<SpaceInfo> => {
    const response = await apiClient.get<SpaceInfo>(`/spaces/${spaceId}`);
    return response.data;
  },

  getAnkiStatus: async (spaceId: string): Promise<AnkiStatus> => {
    const response = await apiClient.get<AnkiStatus>(
      `/spaces/${spaceId}/anki/status`
    );
    return response.data;
  },

  initializeSpace: async (spaceId: string): Promise<AnkiInitializeResponse> => {
    const response = await apiClient.post<AnkiInitializeResponse>(
      `/spaces/${spaceId}/anki/initialize`
    );
    return response.data;
  },
};

