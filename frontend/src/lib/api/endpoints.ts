import apiClient from './client';
import {
  ImportJobResponse,
  ImportJobDetail,
  ImportJobCreateResponse,
  VehicleResponse,
  VehicleUpdate,
  PaginatedResponse,
  PreviewResponse,
  MappingConfig,
  ImportTemplate,
} from '../types/api';

export const jobsApi = {
  create: async (
    file: File,
    mappingConfig?: MappingConfig,
    templateId?: string
  ): Promise<ImportJobCreateResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (mappingConfig) {
      formData.append('mapping_config', JSON.stringify(mappingConfig));
    }
    if (templateId) {
      formData.append('template_id', templateId);
    }

    const response = await apiClient.post<ImportJobCreateResponse>('/imports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  preview: async (file: File): Promise<PreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<PreviewResponse>('/imports/preview', formData, {
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

export const templatesApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    target_table?: string;
  }): Promise<ImportTemplate[]> => {
    const response = await apiClient.get<ImportTemplate[]>('/templates', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ImportTemplate> => {
    const response = await apiClient.get<ImportTemplate>(`/templates/${id}`);
    return response.data;
  },

  create: async (
    name: string,
    target_table: string,
    mapping_config: MappingConfig,
    create_table: boolean = false
  ): Promise<ImportTemplate> => {
    const response = await apiClient.post<ImportTemplate>('/templates', {
      name,
      target_table,
      mapping_config,
      create_table,
    });
    return response.data;
  },

  update: async (
    id: string,
    data: {
      name?: string;
      target_table?: string;
      mapping_config?: MappingConfig;
      create_table?: boolean;
    }
  ): Promise<ImportTemplate> => {
    const response = await apiClient.put<ImportTemplate>(`/templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`);
  },
};
