import { useMutation } from '@tanstack/react-query';
import { jobsApi } from '../endpoints';
import { PreviewResponse } from '../../types/api';

export const usePreviewSpreadsheet = () => {
  return useMutation({
    mutationFn: async (file: File): Promise<PreviewResponse> => {
      return jobsApi.preview(file);
    },
  });
};
