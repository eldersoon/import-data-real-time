'use client';

import { Typography, Input, InputNumber, Space, Button, Card, Row, Col, Popconfirm, message } from 'antd';
import { VehicleTable } from '@/components/VehicleTable';
import { useVehicles } from '@/lib/api/hooks/useVehicles';
import { useClearAllData } from '@/lib/api/hooks/useAdmin';
import { useState } from 'react';
import { SearchOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons';

const { Title } = Typography;

export default function VehiclesPage() {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 10,
    placa: undefined as string | undefined,
    modelo: undefined as string | undefined,
    ano_min: undefined as number | undefined,
    ano_max: undefined as number | undefined,
  });

  const { data, isLoading, refetch } = useVehicles(filters);
  const clearAllData = useClearAllData();

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1, // Reset to first page when filter changes
    }));
  };

  const handleReset = () => {
    setFilters({
      page: 1,
      page_size: 10,
      placa: undefined,
      modelo: undefined,
      ano_min: undefined,
      ano_max: undefined,
    });
  };

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
          Veículos Importados
        </Title>
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
            Limpar Todos os Dados
          </Button>
        </Popconfirm>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Input
              placeholder="Filtrar por placa"
              value={filters.placa}
              onChange={(e) => handleFilterChange('placa', e.target.value || undefined)}
              allowClear
            />
          </Col>
          <Col span={6}>
            <Input
              placeholder="Filtrar por modelo"
              value={filters.modelo}
              onChange={(e) => handleFilterChange('modelo', e.target.value || undefined)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <InputNumber
              placeholder="Ano mínimo"
              style={{ width: '100%' }}
              value={filters.ano_min}
              onChange={(value) => handleFilterChange('ano_min', value || undefined)}
              min={1900}
            />
          </Col>
          <Col span={4}>
            <InputNumber
              placeholder="Ano máximo"
              style={{ width: '100%' }}
              value={filters.ano_max}
              onChange={(value) => handleFilterChange('ano_max', value || undefined)}
              min={1900}
            />
          </Col>
          <Col span={4}>
            <Space>
              <Button icon={<SearchOutlined />} type="primary" onClick={() => refetch()}>
                Buscar
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                Limpar
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <VehicleTable
        vehicles={data?.data || []}
        loading={isLoading}
        total={data?.total || 0}
        page={filters.page}
        pageSize={filters.page_size}
        onPageChange={(page, pageSize) => {
          setFilters((prev) => ({ ...prev, page, page_size: pageSize }));
        }}
        onFilterChange={setFilters}
      />
    </div>
  );
}
