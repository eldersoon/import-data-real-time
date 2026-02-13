import { useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../endpoints';

export const useClearAllData = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => adminApi.clearAllData(),
    onSuccess: () => {
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries();
    },
  });
};
