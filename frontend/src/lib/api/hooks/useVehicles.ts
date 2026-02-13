import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { vehiclesApi } from '../endpoints';
import { VehicleResponse, VehicleUpdate } from '../../types/api';

export const useVehicles = (params?: {
  page?: number;
  page_size?: number;
  placa?: string;
  modelo?: string;
  ano_min?: number;
  ano_max?: number;
}) => {
  return useQuery({
    queryKey: ['vehicles', params],
    queryFn: () => vehiclesApi.list(params),
  });
};

export const useUpdateVehicle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: VehicleUpdate }) =>
      vehiclesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    },
  });
};

export const useDeleteVehicle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => vehiclesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
    },
  });
};
