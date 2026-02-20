import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { entitiesApi } from '../endpoints';
import { DynamicEntityResponse, DynamicEntityUpdate, PaginatedResponse } from '../../types/api';

export const useEntities = (visibleOnly?: boolean) => {
  return useQuery({
    queryKey: ['entities', { visibleOnly }],
    queryFn: () => entitiesApi.list(visibleOnly),
  });
};

export const useEntity = (tableName: string) => {
  return useQuery({
    queryKey: ['entities', tableName],
    queryFn: () => entitiesApi.getByTableName(tableName),
    enabled: !!tableName,
  });
};

export const useUpdateEntityVisibility = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tableName, isVisible }: { tableName: string; isVisible: boolean }) =>
      entitiesApi.updateVisibility(tableName, isVisible),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
    },
  });
};

export const useUpdateEntityDisplayName = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tableName, displayName }: { tableName: string; displayName: string }) =>
      entitiesApi.updateDisplayName(tableName, displayName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
    },
  });
};

export const useUpdateEntity = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tableName, data }: { tableName: string; data: DynamicEntityUpdate }) =>
      entitiesApi.update(tableName, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
    },
  });
};

export const useEntityData = (
  tableName: string,
  params?: {
    page?: number;
    page_size?: number;
  }
) => {
  return useQuery({
    queryKey: ['entities', tableName, 'data', params],
    queryFn: () => entitiesApi.listData(tableName, params),
    enabled: !!tableName,
  });
};

export const useEntityRecord = (tableName: string, id: string) => {
  return useQuery({
    queryKey: ['entities', tableName, 'data', id],
    queryFn: () => entitiesApi.getDataById(tableName, id),
    enabled: !!tableName && !!id,
  });
};

export const useCreateEntityRecord = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tableName, data }: { tableName: string; data: Record<string, any> }) =>
      entitiesApi.createData(tableName, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['entities', variables.tableName, 'data'] });
    },
  });
};

export const useUpdateEntityRecord = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tableName,
      id,
      data,
    }: {
      tableName: string;
      id: string;
      data: Record<string, any>;
    }) => entitiesApi.updateData(tableName, id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['entities', variables.tableName, 'data'] });
      queryClient.invalidateQueries({
        queryKey: ['entities', variables.tableName, 'data', variables.id],
      });
    },
  });
};

export const useDeleteEntityRecord = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tableName, id }: { tableName: string; id: string }) =>
      entitiesApi.deleteData(tableName, id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['entities', variables.tableName, 'data'] });
    },
  });
};
