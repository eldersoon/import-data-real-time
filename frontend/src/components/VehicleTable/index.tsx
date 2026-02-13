'use client';

import { Table, Button, Space, Popconfirm, Input, InputNumber, Form, Modal, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { VehicleResponse, VehicleUpdate } from '@/lib/types/api';
import { formatCurrency, formatDateTime } from '@/lib/utils/formatters';
import { useState } from 'react';
import { useUpdateVehicle, useDeleteVehicle } from '@/lib/api/hooks/useVehicles';

interface VehicleTableProps {
  vehicles: VehicleResponse[];
  loading?: boolean;
  total?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number, pageSize: number) => void;
  onFilterChange?: (filters: any) => void;
}

export const VehicleTable: React.FC<VehicleTableProps> = ({
  vehicles,
  loading,
  total = 0,
  page = 1,
  pageSize = 10,
  onPageChange,
  onFilterChange,
}) => {
  const [editingVehicle, setEditingVehicle] = useState<VehicleResponse | null>(null);
  const [form] = Form.useForm();
  const updateVehicle = useUpdateVehicle();
  const deleteVehicle = useDeleteVehicle();

  const handleEdit = (vehicle: VehicleResponse) => {
    setEditingVehicle(vehicle);
    form.setFieldsValue({
      modelo: vehicle.modelo,
      valor_fipe: vehicle.valor_fipe,
    });
  };

  const handleUpdate = async () => {
    if (!editingVehicle) return;

    try {
      const values = await form.validateFields();
      await updateVehicle.mutateAsync({
        id: editingVehicle.id,
        data: values as VehicleUpdate,
      });
      message.success('Veículo atualizado com sucesso!');
      setEditingVehicle(null);
      form.resetFields();
    } catch (error) {
      // Error já é tratado
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteVehicle.mutateAsync(id);
      message.success('Veículo deletado com sucesso!');
    } catch (error) {
      // Error já é tratado
    }
  };

  const columns: ColumnsType<VehicleResponse> = [
    {
      title: 'Modelo',
      dataIndex: 'modelo',
      key: 'modelo',
    },
    {
      title: 'Placa',
      dataIndex: 'placa',
      key: 'placa',
    },
    {
      title: 'Ano',
      dataIndex: 'ano',
      key: 'ano',
    },
    {
      title: 'Valor FIPE',
      dataIndex: 'valor_fipe',
      key: 'valor_fipe',
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Criado em',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => formatDateTime(date),
    },
    {
      title: 'Ações',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Editar
          </Button>
          <Popconfirm
            title="Tem certeza que deseja deletar este veículo?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sim"
            cancelText="Não"
          >
            <Button
              icon={<DeleteOutlined />}
              danger
              size="small"
              loading={deleteVehicle.isPending}
            >
              Deletar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Table
        columns={columns}
        dataSource={vehicles}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} veículos`,
          pageSizeOptions: ['10', '20', '50', '100'],
          onChange: (page, size) => {
            if (onPageChange) {
              onPageChange(page, size);
            }
          },
        }}
      />

      <Modal
        title="Editar Veículo"
        open={!!editingVehicle}
        onOk={handleUpdate}
        onCancel={() => {
          setEditingVehicle(null);
          form.resetFields();
        }}
        confirmLoading={updateVehicle.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="modelo"
            label="Modelo"
            rules={[{ required: true, message: 'Por favor, insira o modelo!' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="valor_fipe"
            label="Valor FIPE"
            rules={[
              { required: true, message: 'Por favor, insira o valor FIPE!' },
              { type: 'number', min: 0.01, message: 'Valor deve ser maior que zero!' },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              prefix="R$"
              min={0.01}
              step={0.01}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};
