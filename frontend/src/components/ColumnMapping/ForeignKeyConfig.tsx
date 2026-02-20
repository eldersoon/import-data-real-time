'use client';

import { Input, Select, Space } from 'antd';
import { ForeignKeyConfig as FKConfig } from '@/lib/types/api';

interface ForeignKeyConfigProps {
  config: FKConfig;
  onChange: (config: FKConfig) => void;
}

export const ForeignKeyConfig: React.FC<ForeignKeyConfigProps> = ({ config, onChange }) => {
  return (
    <Space direction="vertical" size="small">
      <Input
        placeholder="Tabela de referência"
        value={config.table}
        onChange={(e) => onChange({ ...config, table: e.target.value })}
        size="small"
      />
      <Input
        placeholder="Coluna de lookup"
        value={config.lookup_column}
        onChange={(e) => onChange({ ...config, lookup_column: e.target.value })}
        size="small"
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
