import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { templatesApi } from '../endpoints';
import { ImportTemplate, MappingConfig } from '../../types/api';

export const useTemplates = (params?: { skip?: number; limit?: number; target_table?: string }) => {
  return useQuery({
    queryKey: ['templates', params],
    queryFn: async () => {
      return templatesApi.list(params);
    },
  });
};

export const useTemplate = (id: string) => {
  return useQuery({
    queryKey: ['template', id],
    queryFn: async () => {
      return templatesApi.getById(id);
    },
    enabled: !!id,
  });
};

export const useCreateTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      name: string;
      target_table: string;
      mapping_config: MappingConfig;
      create_table?: boolean;
    }): Promise<ImportTemplate> => {
      return templatesApi.create(data.name, data.target_table, data.mapping_config, data.create_table || false);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};

export const useUpdateTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: {
      id: string;
      name?: string;
      target_table?: string;
      mapping_config?: MappingConfig;
      create_table?: boolean;
    }): Promise<ImportTemplate> => {
      return templatesApi.update(id, data);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      queryClient.invalidateQueries({ queryKey: ['template', variables.id] });
    },
  });
};

export const useDeleteTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      return templatesApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
};
