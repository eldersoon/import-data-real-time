'use client';

import { Table, Card, Typography, Tag } from 'antd';
import { PreviewResponse } from '@/lib/types/api';

const { Title } = Typography;

interface SpreadsheetPreviewProps {
  preview: PreviewResponse;
}

export const SpreadsheetPreview: React.FC<SpreadsheetPreviewProps> = ({ preview }) => {
  // Table columns for preview
  const previewColumns = preview.columns.map((col) => ({
    title: col.name,
    dataIndex: col.name,
    key: col.name,
    render: (value: any) => {
      if (value === null || value === undefined) {
        return <span style={{ color: '#999' }}>null</span>;
      }
      return String(value);
    },
  }));

  // Table columns for column info
  const columnInfoColumns = [
    {
      title: 'Coluna',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Tipo Sugerido',
      dataIndex: 'suggested_type',
      key: 'suggested_type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Valores de Exemplo',
      dataIndex: 'sample_values',
      key: 'sample_values',
      render: (values: any[]) => (
        <span>{values.slice(0, 3).join(', ')}{values.length > 3 ? '...' : ''}</span>
      ),
    },
    {
      title: 'Nulos',
      dataIndex: 'null_count',
      key: 'null_count',
      render: (count: number, record: any) => (
        <span>{count} / {record.total_count}</span>
      ),
    },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Title level={4}>Informações do Arquivo</Title>
        <p>
          <strong>Total de colunas:</strong> {preview.total_columns}
        </p>
        <p>
          <strong>Total de linhas:</strong> {preview.total_rows}
        </p>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Title level={4}>Colunas Detectadas</Title>
        <Table
          dataSource={preview.columns.map((col, idx) => ({ ...col, key: idx }))}
          columns={columnInfoColumns}
          pagination={false}
          size="small"
        />
      </Card>

      <Card>
        <Title level={4}>Preview dos Dados (Primeiras 10 linhas)</Title>
        <Table
          dataSource={preview.preview_rows.map((row, idx) => ({ ...row, key: idx }))}
          columns={previewColumns}
          pagination={false}
          scroll={{ x: 'max-content' }}
          size="small"
        />
      </Card>
    </div>
  );
};
