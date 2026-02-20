'use client';

import { useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTemplates, useDeleteTemplate } from '@/lib/api/hooks/useTemplates';
import { ImportTemplate } from '@/lib/types/api';

export default function TemplatesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ImportTemplate | null>(null);
  const { data: templates, isLoading } = useTemplates();
  const deleteTemplate = useDeleteTemplate();

  const handleDelete = async (id: string) => {
    try {
      await deleteTemplate.mutateAsync(id);
      message.success('Template deletado com sucesso');
    } catch (error: any) {
      message.error(`Erro ao deletar template: ${error?.response?.data?.detail || error.message}`);
    }
  };

  const columns = [
    {
      title: 'Nome',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Tabela Destino',
      dataIndex: 'target_table',
      key: 'target_table',
    },
    {
      title: 'Criar Tabela',
      dataIndex: 'create_table',
      key: 'create_table',
      render: (value: boolean) => (value ? 'Sim' : 'Não'),
    },
    {
      title: 'Colunas',
      key: 'columns',
      render: (_: any, record: ImportTemplate) => record.mapping_config.columns.length,
    },
    {
      title: 'Ações',
      key: 'actions',
      render: (_: any, record: ImportTemplate) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            onClick={() => {
              setEditingTemplate(record);
              setIsModalOpen(true);
            }}
          >
            Editar
          </Button>
          <Popconfirm
            title="Tem certeza que deseja deletar este template?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sim"
            cancelText="Não"
          >
            <Button danger icon={<DeleteOutlined />}>
              Deletar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h1>Templates de Importação</h1>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          Novo Template
        </Button>
      </div>
      <Table
        dataSource={templates}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />
      <Modal
        title={editingTemplate ? 'Editar Template' : 'Novo Template'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          setEditingTemplate(null);
        }}
        footer={null}
        width={800}
      >
        <p>Use a página de upload configurável para criar templates. Eles serão salvos automaticamente após a importação.</p>
      </Modal>
    </div>
  );
}
