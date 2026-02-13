'use client';

import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { StatusBadge } from '../StatusBadge';
import { ImportJobResponse } from '@/lib/types/api';
import { formatDateTime, calculateProgress } from '@/lib/utils/formatters';
import Link from 'next/link';
import { EyeOutlined } from '@ant-design/icons';

interface JobTableProps {
  jobs: ImportJobResponse[];
  loading?: boolean;
}

export const JobTable: React.FC<JobTableProps> = ({ jobs, loading }) => {
  const columns: ColumnsType<ImportJobResponse> = [
    {
      title: 'Arquivo',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <StatusBadge status={status} />,
    },
    {
      title: 'Progresso',
      key: 'progress',
      render: (_, record) => {
        if (!record.total_rows) return '-';
        const progress = calculateProgress(record.processed_rows, record.total_rows);
        return `${record.processed_rows} / ${record.total_rows} (${progress}%)`;
      },
    },
    {
      title: 'Erros',
      dataIndex: 'error_rows',
      key: 'error_rows',
      render: (errors) => (
        <Tag color={errors > 0 ? 'red' : 'green'}>{errors}</Tag>
      ),
    },
    {
      title: 'Data',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => formatDateTime(date),
    },
    {
      title: 'Ações',
      key: 'actions',
      render: (_, record) => (
        <Link href={`/jobs/${record.id}`}>
          <EyeOutlined style={{ fontSize: 16, color: '#1890ff' }} />
        </Link>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={jobs}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 10 }}
    />
  );
};
