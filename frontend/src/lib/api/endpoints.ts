import apiClient from './client';
import {
  ImportJobResponse,
  ImportJobDetail,
  ImportJobCreateResponse,
  VehicleResponse,
  VehicleUpdate,
  PaginatedResponse,
} from '../types/api';

export const jobsApi = {
  create: async (file: File): Promise<ImportJobCreateResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<ImportJobCreateResponse>('/imports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  list: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<ImportJobResponse[]> => {
    const response = await apiClient.get<ImportJobResponse[]>('/imports', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ImportJobDetail> => {
    const response = await apiClient.get<ImportJobDetail>(`/imports/${id}`);
    return response.data;
  },
};

export const vehiclesApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    placa?: string;
    modelo?: string;
    ano_min?: number;
    ano_max?: number;
  }): Promise<PaginatedResponse<VehicleResponse>> => {
    const response = await apiClient.get<PaginatedResponse<VehicleResponse>>('/vehicles', {
      params,
    });
    return response.data;
  },

  getById: async (id: string): Promise<VehicleResponse> => {
    const response = await apiClient.get<VehicleResponse>(`/vehicles/${id}`);
    return response.data;
  },

  update: async (id: string, data: VehicleUpdate): Promise<VehicleResponse> => {
    const response = await apiClient.put<VehicleResponse>(`/vehicles/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/vehicles/${id}`);
  },
};

export const adminApi = {
  clearAllData: async (): Promise<void> => {
    await apiClient.delete('/admin/clear-data');
  },
};
