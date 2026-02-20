import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi } from '../endpoints';
import { ImportJobResponse, ImportJobDetail, MappingConfig } from '../../types/api';

export const useJobs = (
  params?: {
    skip?: number;
    limit?: number;
    status?: string;
  },
  options?: {
    refetchInterval?: number | false | ((query: any) => number | false);
    enabled?: boolean;
  }
) => {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: () => jobsApi.list(params),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
  });
};

export const useJob = (id: string, options?: { enabled?: boolean; refetchInterval?: number }) => {
  return useQuery({
    queryKey: ['job', id],
    queryFn: () => jobsApi.getById(id),
    enabled: options?.enabled !== false,
    refetchInterval: options?.refetchInterval,
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, mappingConfig, templateId }: { file: File; mappingConfig?: MappingConfig; templateId?: string }) =>
      jobsApi.create(file, mappingConfig, templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
