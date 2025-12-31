import { apiClient } from "./client";

export interface RunRequest {
  mode?: string;
}

export interface RunResponse {
  run_id: string;
  space_id: string;
  mode: string;
  status: "running" | "completed" | "failed";
  today_count?: number;
  new_accepted?: number;
  degraded: boolean;
  degraded_reason?: string;
  error_message?: string;
  error_code?: string;
  error_phase?: number;
  started_at: string;
  completed_at?: string;
}

export const runsApi = {
  create: async (
    spaceId: string,
    request: RunRequest
  ): Promise<RunResponse> => {
    const response = await apiClient.post<RunResponse>(
      `/spaces/${spaceId}/runs`,
      request
    );
    return response.data;
  },

  get: async (spaceId: string, runId: string): Promise<RunResponse> => {
    const response = await apiClient.get<RunResponse>(
      `/spaces/${spaceId}/runs/${runId}`
    );
    return response.data;
  },

  list: async (spaceId: string): Promise<RunResponse[]> => {
    const response = await apiClient.get<RunResponse[]>(
      `/spaces/${spaceId}/runs`
    );
    return response.data;
  },

  checkPrerequisites: async (spaceId: string): Promise<PrerequisitesCheck> => {
    const response = await apiClient.get<PrerequisitesCheck>(
      `/spaces/${spaceId}/runs/prerequisites`
    );
    return response.data;
  },
};

export interface PrerequisitesCheck {
  all_passed: boolean;
  checks: Record<string, any>;
  warnings: string[];
  errors: string[];
}

