'use client';

import { Select, Space } from 'antd';
import { ForeignKeyConfig as FKConfig } from '@/lib/types/api';
import { useTables, useTableColumns } from '@/lib/api/hooks/useMetadata';

interface ForeignKeyConfigProps {
  config: FKConfig;
  onChange: (config: FKConfig) => void;
}

export const ForeignKeyConfig: React.FC<ForeignKeyConfigProps> = ({ config, onChange }) => {
  const { data: tablesData, isLoading: tablesLoading } = useTables();
  const { data: columnsData, isLoading: columnsLoading } = useTableColumns(config.table);

  const tables = tablesData?.tables || [];
  const columns = columnsData?.columns || [];

  const handleTableChange = (tableName: string) => {
    // Reset lookup_column when table changes
    onChange({ ...config, table: tableName, lookup_column: '' });
  };

  const handleColumnChange = (columnName: string) => {
    onChange({ ...config, lookup_column: columnName });
  };

  return (
    <Space direction="vertical" size="small" style={{ width: '100%' }}>
      <Select
        placeholder="Selecione a tabela de referência"
        value={config.table || undefined}
        onChange={handleTableChange}
        size="small"
        style={{ width: '100%' }}
        loading={tablesLoading}
        showSearch
        filterOption={(input, option) =>
          (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
        }
        options={tables.map((table) => ({
          value: table,
          label: table,
        }))}
      />
      <Select
        placeholder="Selecione a coluna de lookup"
        value={config.lookup_column || undefined}
        onChange={handleColumnChange}
        size="small"
        style={{ width: '100%' }}
        loading={columnsLoading}
        disabled={!config.table}
        showSearch
        filterOption={(input, option) =>
          (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
        }
        options={columns.map((col) => ({
          value: col.column_name,
          label: `${col.column_name} (${col.data_type})`,
        }))}
      />
      <Select
        value={config.on_missing}
        onChange={(value) => onChange({ ...config, on_missing: value })}
        size="small"
        style={{ width: '100%' }}
        options={[
          { value: 'error', label: 'Erro se não encontrado' },
          { value: 'ignore', label: 'Ignorar se não encontrado' },
          { value: 'create', label: 'Criar se não encontrado' },
        ]}
      />
    </Space>
  );
};
