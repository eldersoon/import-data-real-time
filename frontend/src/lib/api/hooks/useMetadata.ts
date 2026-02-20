import { useQuery } from '@tanstack/react-query';
import { metadataApi } from '../endpoints';
import { TableInfoResponse } from '../../types/api';

export const useTables = () => {
  return useQuery({
    queryKey: ['metadata', 'tables'],
    queryFn: () => metadataApi.listTables(),
  });
};

export const useTableColumns = (tableName: string) => {
  return useQuery<TableInfoResponse>({
    queryKey: ['metadata', 'tables', tableName, 'columns'],
    queryFn: () => metadataApi.getTableColumns(tableName),
    enabled: !!tableName,
  });
};
