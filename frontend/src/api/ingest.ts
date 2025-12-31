import { apiClient } from "./client";

export interface IngestResponse {
  ingest_id: string;
  space_id: string;
  status: string;
  sources_count: number;
  new_sources_count: number;
  filename?: string;
  queue_path: string;
  ingest_log_path?: string;
  started_at: string;
  completed_at?: string;
}

export interface UploadResponse {
  filename: string;
  file_path: string;
  size: number;
  uploaded_at: string;
}

export interface UploadedFileInfo {
  filename: string;
  file_path: string;
  size: number;
  modified_at: string;
}

export interface UploadedFilesResponse {
  files: UploadedFileInfo[];
}

export interface IngestHistoryItem {
  ingest_id: string;
  source: string;
  sources_count: number;
  new_sources_count: number;
  filename?: string;
  started_at: string;
}

export interface IngestHistoryResponse {
  ingests: IngestHistoryItem[];
}

export const ingestApi = {
  upload: async (spaceId: string, file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<UploadResponse>(
      `/spaces/${spaceId}/ingest/upload`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  ingest: async (
    spaceId: string,
    filePath: string,
    title?: string
  ): Promise<IngestResponse> => {
    const response = await apiClient.post<IngestResponse>(
      `/spaces/${spaceId}/ingest`,
      {
        file_path: filePath,
        title,
      }
    );
    return response.data;
  },

  listFiles: async (spaceId: string): Promise<UploadedFilesResponse> => {
    const response = await apiClient.get<UploadedFilesResponse>(
      `/spaces/${spaceId}/ingest/files`
    );
    return response.data;
  },

  getStatus: async (
    spaceId: string,
    ingestId: string
  ): Promise<IngestResponse> => {
    const response = await apiClient.get<IngestResponse>(
      `/spaces/${spaceId}/ingest/status/${ingestId}`
    );
    return response.data;
  },

  getHistory: async (spaceId: string): Promise<IngestHistoryResponse> => {
    const response = await apiClient.get<IngestHistoryResponse>(
      `/spaces/${spaceId}/ingest/history`
    );
    return response.data;
  },
};

