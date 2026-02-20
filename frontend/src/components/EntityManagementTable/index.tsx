'use client';

import { Table, Button, Space, Popconfirm, Input, Switch, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useUpdateEntity, useUpdateEntityVisibility, useEntities } from '@/lib/api/hooks/useEntities';
import { DynamicEntityResponse } from '@/lib/types/api';
import { formatDateTime } from '@/lib/utils/formatters';

interface EntityManagementTableProps {
  onEdit?: (entity: DynamicEntityResponse) => void;
}

export const EntityManagementTable: React.FC<EntityManagementTableProps> = ({ onEdit }) => {
  const [editingName, setEditingName] = useState<{ tableName: string; value: string } | null>(null);
  const { data: entities = [], isLoading, refetch } = useEntities(false); // Get all entities
  const updateEntity = useUpdateEntity();
  const updateVisibility = useUpdateEntityVisibility();

  const handleVisibilityToggle = async (tableName: string, isVisible: boolean) => {
    try {
      await updateVisibility.mutateAsync({ tableName, isVisible });
      message.success('Visibilidade atualizada com sucesso!');
    } catch (error) {
      // Error já é tratado
    }
  };

  const handleDisplayNameEdit = (entity: DynamicEntityResponse) => {
    setEditingName({ tableName: entity.table_name, value: entity.display_name });
  };

  const handleDisplayNameSave = async () => {
    if (!editingName) return;

    try {
      await updateEntity.mutateAsync({
        tableName: editingName.tableName,
        data: { display_name: editingName.value },
      });
      message.success('Nome de exibição atualizado com sucesso!');
      setEditingName(null);
    } catch (error) {
      // Error já é tratado
    }
  };

  const handleDisplayNameCancel = () => {
    setEditingName(null);
  };

  const columns: ColumnsType<DynamicEntityResponse> = [
    {
      title: 'Nome de Exibição',
      dataIndex: 'display_name',
      key: 'display_name',
      render: (text, record) => {
        if (editingName?.tableName === record.table_name) {
          return (
            <Input
              value={editingName.value}
              onChange={(e) => setEditingName({ ...editingName, value: e.target.value })}
              onPressEnter={handleDisplayNameSave}
              onBlur={handleDisplayNameSave}
              autoFocus
            />
          );
        }
        return (
          <Space>
            <span>{text}</span>
            <Button
              type="link"
              icon={<EditOutlined />}
              size="small"
              onClick={() => handleDisplayNameEdit(record)}
            />
          </Space>
        );
      },
    },
    {
      title: 'Nome da Tabela',
      dataIndex: 'table_name',
      key: 'table_name',
    },
    {
      title: 'Visível',
      dataIndex: 'is_visible',
      key: 'is_visible',
      render: (isVisible, record) => (
        <Switch
          checked={isVisible}
          onChange={(checked) => handleVisibilityToggle(record.table_name, checked)}
          loading={updateVisibility.isPending}
        />
      ),
    },
    {
      title: 'Descrição',
      dataIndex: 'description',
      key: 'description',
      render: (text) => text || '-',
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
          {onEdit && (
            <Button
              icon={<EditOutlined />}
              onClick={() => onEdit(record)}
              size="small"
            >
              Editar
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={entities}
      rowKey="table_name"
      loading={isLoading}
      pagination={{
        pageSize: 20,
        showSizeChanger: true,
        showTotal: (total) => `Total: ${total} entidades`,
      }}
    />
  );
};
