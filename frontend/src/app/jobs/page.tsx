'use client';

import { Typography, Select, Space, Spin, Button, Popconfirm, message } from 'antd';
import { JobTable } from '@/components/JobTable';
import { useJobsSSE } from '@/hooks/useJobsSSE';
import { useClearAllData } from '@/lib/api/hooks/useAdmin';
import { useState } from 'react';
import { JobStatus } from '@/lib/types/api';
import { DeleteOutlined } from '@ant-design/icons';

const { Title } = Typography;

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<JobStatus | undefined>();
  const { jobs, isLoading, refetch } = useJobsSSE({
    limit: 100,
    status: statusFilter,
  });
  const clearAllData = useClearAllData();

  const handleClearAllData = async () => {
    try {
      await clearAllData.mutateAsync();
      message.success('Todos os dados foram deletados com sucesso!');
      refetch();
    } catch (error) {
      // Error já é tratado pelo interceptor
    }
  };

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>
          Jobs de Importação
        </Title>
        <Space>
          <Select
            placeholder="Filtrar por status"
            allowClear
            style={{ width: 200 }}
            onChange={(value) => setStatusFilter(value)}
            options={[
              { label: 'Pendente', value: 'pending' },
              { label: 'Em Progresso', value: 'processing' },
              { label: 'Concluído', value: 'completed' },
              { label: 'Falhou', value: 'failed' },
            ]}
          />
          <Popconfirm
            title="Tem certeza que deseja deletar TODOS os dados?"
            description="Isso irá deletar todos os veículos, jobs e logs. Esta ação não pode ser desfeita!"
            onConfirm={handleClearAllData}
            okText="Sim, deletar tudo"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
          >
            <Button
              icon={<DeleteOutlined />}
              danger
              loading={clearAllData.isPending}
            >
              Limpar Dados
            </Button>
          </Popconfirm>
        </Space>
      </Space>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Spin size="large" />
        </div>
      ) : (
        <JobTable jobs={jobs || []} loading={isLoading} />
      )}
    </div>
  );
}
