'use client';

import { Table, Input, Select, Switch, Button, Space, Card, Typography } from 'antd';
import { ColumnMapping, ColumnInfo } from '@/lib/types/api';
import { ForeignKeyConfig } from './ForeignKeyConfig';

const { Title } = Typography;

interface ColumnMappingProps {
  columns: ColumnInfo[];
  mappings: ColumnMapping[];
  onChange: (mappings: ColumnMapping[]) => void;
  targetTable: string;
  onTargetTableChange: (table: string) => void;
  onCreateTableChange: (create: boolean) => void;
  createTable: boolean;
}

const TYPE_OPTIONS = [
  { value: 'string', label: 'String' },
  { value: 'int', label: 'Integer' },
  { value: 'float', label: 'Float' },
  { value: 'decimal', label: 'Decimal' },
  { value: 'date', label: 'Date' },
  { value: 'datetime', label: 'DateTime' },
  { value: 'boolean', label: 'Boolean' },
  { value: 'fk', label: 'Foreign Key' },
];

export const ColumnMapping: React.FC<ColumnMappingProps> = ({
  columns,
  mappings,
  onChange,
  targetTable,
  onTargetTableChange,
  onCreateTableChange,
  createTable,
}) => {
  const handleMappingChange = (index: number, field: keyof ColumnMapping, value: any) => {
    const newMappings = [...mappings];
    newMappings[index] = { ...newMappings[index], [field]: value };
    
    // If type changed to/from fk, handle fk config
    if (field === 'type') {
      if (value === 'fk') {
        newMappings[index].fk = {
          table: '',
          lookup_column: '',
          on_missing: 'error',
        };
      } else {
        delete newMappings[index].fk;
      }
    }
    
    onChange(newMappings);
  };

  const handleAddMapping = (column: ColumnInfo) => {
    const newMapping: ColumnMapping = {
      sheet_column: column.name,
      db_column: column.name.toLowerCase().replace(/\s+/g, '_'),
      type: column.suggested_type as any,
      required: false,
    };
    onChange([...mappings, newMapping]);
  };

  const handleRemoveMapping = (index: number) => {
    const newMappings = mappings.filter((_, i) => i !== index);
    onChange(newMappings);
  };

  const unmappedColumns = columns.filter(
    (col) => !mappings.some((m) => m.sheet_column === col.name)
  );

  const mappingColumns = [
    {
      title: 'Coluna da Planilha',
      dataIndex: 'sheet_column',
      key: 'sheet_column',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Coluna no Banco',
      dataIndex: 'db_column',
      key: 'db_column',
      render: (text: string, record: ColumnMapping, index: number) => (
        <Input
          value={text}
          onChange={(e) => handleMappingChange(index, 'db_column', e.target.value)}
          placeholder="nome_da_coluna"
        />
      ),
    },
    {
      title: 'Tipo',
      dataIndex: 'type',
      key: 'type',
      render: (type: string, record: ColumnMapping, index: number) => (
        <Select
          value={type}
          onChange={(value) => handleMappingChange(index, 'type', value)}
          options={TYPE_OPTIONS}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: 'Obrigatório',
      dataIndex: 'required',
      key: 'required',
      render: (required: boolean, record: ColumnMapping, index: number) => (
        <Switch
          checked={required}
          onChange={(checked) => handleMappingChange(index, 'required', checked)}
        />
      ),
    },
    {
      title: 'Configuração FK',
      key: 'fk',
      render: (_: any, record: ColumnMapping, index: number) => {
        if (record.type !== 'fk') return null;
        return (
          <ForeignKeyConfig
            config={record.fk!}
            onChange={(fk) => handleMappingChange(index, 'fk', fk)}
          />
        );
      },
    },
    {
      title: 'Ações',
      key: 'actions',
      render: (_: any, record: ColumnMapping, index: number) => (
        <Button danger onClick={() => handleRemoveMapping(index)}>
          Remover
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Title level={4}>Configuração da Tabela Destino</Title>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <label>Nome da Tabela: </label>
            <Input
              value={targetTable}
              onChange={(e) => onTargetTableChange(e.target.value)}
              placeholder="tb_exemplo"
              style={{ width: 300 }}
            />
          </div>
          <div>
            <label>Criar tabela se não existir: </label>
            <Switch
              checked={createTable}
              onChange={onCreateTableChange}
            />
          </div>
        </Space>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Title level={4}>Mapeamento de Colunas</Title>
        {mappings.length === 0 ? (
          <p>Nenhuma coluna mapeada. Adicione colunas abaixo.</p>
        ) : (
          <Table
            dataSource={mappings.map((m, idx) => ({ ...m, key: idx }))}
            columns={mappingColumns}
            pagination={false}
          />
        )}
      </Card>

      {unmappedColumns.length > 0 && (
        <Card>
          <Title level={4}>Colunas Não Mapeadas</Title>
          <Space wrap>
            {unmappedColumns.map((col) => (
              <Button
                key={col.name}
                onClick={() => handleAddMapping(col)}
                type="dashed"
              >
                + {col.name}
              </Button>
            ))}
          </Space>
        </Card>
      )}
    </div>
  );
};
