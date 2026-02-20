'use client';

import React from 'react';
import { Table, Input, Select, Switch, Button, Space, Card, Typography } from 'antd';
import { ColumnMapping as ColumnMappingType, ColumnInfo } from '@/lib/types/api';
import { ForeignKeyConfig } from './ForeignKeyConfig';

const { Title, Text } = Typography;

interface ColumnMappingProps {
  columns: ColumnInfo[];
  mappings: ColumnMappingType[];
  onChange: (mappings: ColumnMappingType[]) => void;
  targetTable: string;
  onTargetTableChange: (table: string) => void;
  onCreateTableChange: (create: boolean) => void;
  createTable: boolean;
  entityDisplayName?: string;
  onEntityDisplayNameChange?: (name: string) => void;
  entityDescription?: string;
  onEntityDescriptionChange?: (description: string) => void;
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
  entityDisplayName,
  onEntityDisplayNameChange,
  entityDescription,
  onEntityDescriptionChange,
}) => {
  const handleMappingChange = (index: number, field: keyof ColumnMappingType, value: any) => {
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
    const newMapping: ColumnMappingType = {
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
      render: (text: string, record: ColumnMappingType, index: number) => (
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
      render: (type: string, record: ColumnMappingType, index: number) => (
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
      render: (required: boolean, record: ColumnMappingType, index: number) => (
        <Switch
          checked={required}
          onChange={(checked) => handleMappingChange(index, 'required', checked)}
        />
      ),
    },
    {
      title: 'Configuração FK',
      key: 'fk',
      render: (_: any, record: ColumnMappingType, index: number) => {
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
      render: (_: any, record: ColumnMappingType, index: number) => (
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
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>Nome da Tabela: </label>
            <Input
              value={targetTable}
              onChange={(e) => onTargetTableChange(e.target.value)}
              placeholder="tb_exemplo"
              style={{ width: '100%', maxWidth: 400 }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>Criar tabela se não existir: </label>
            <Switch
              checked={createTable}
              onChange={onCreateTableChange}
            />
          </div>
          {createTable && (
            <Card type="inner" style={{ backgroundColor: '#f0f2f5', marginTop: 16 }}>
              <Title level={5} style={{ marginTop: 0 }}>Informações da Entidade</Title>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                    Nome de Exibição da Entidade <span style={{ color: 'red' }}>*</span>:
                  </label>
                  <Input
                    value={entityDisplayName || ''}
                    onChange={(e) => onEntityDisplayNameChange?.(e.target.value)}
                    placeholder="Ex: Usuários, Produtos, Clientes, etc."
                    style={{ width: '100%', maxWidth: 400 }}
                    required
                  />
                  <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                    Este nome aparecerá no menu lateral
                  </Text>
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                    Descrição da Entidade (opcional):
                  </label>
                  <Input.TextArea
                    value={entityDescription || ''}
                    onChange={(e) => onEntityDescriptionChange?.(e.target.value)}
                    placeholder="Descrição da entidade que aparecerá no menu"
                    rows={3}
                    style={{ width: '100%', maxWidth: 400 }}
                  />
                </div>
              </Space>
            </Card>
          )}
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
