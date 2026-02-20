'use client';

import { Table, Button, Space, Popconfirm, Form, Modal, message, Input, InputNumber, DatePicker, Select } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useState, useMemo } from 'react';
import { useUpdateEntityRecord, useDeleteEntityRecord } from '@/lib/api/hooks/useEntities';
import { useTableColumns } from '@/lib/api/hooks/useMetadata';
import { formatDateTime } from '@/lib/utils/formatters';
import dayjs from 'dayjs';

interface EntityTableProps {
  tableName: string;
  data: Record<string, any>[];
  loading?: boolean;
  total?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number, pageSize: number) => void;
}

export const EntityTable: React.FC<EntityTableProps> = ({
  tableName,
  data,
  loading,
  total = 0,
  page = 1,
  pageSize = 10,
  onPageChange,
}) => {
  const [editingRecord, setEditingRecord] = useState<Record<string, any> | null>(null);
  const [form] = Form.useForm();
  const updateRecord = useUpdateEntityRecord();
  const deleteRecord = useDeleteEntityRecord();
  const { data: tableInfo } = useTableColumns(tableName);

  const handleEdit = (record: Record<string, any>) => {
    setEditingRecord(record);
    const formValues: Record<string, any> = {};
    
    // Convert values for form fields
    tableInfo?.columns.forEach((col) => {
      const value = record[col.column_name];
      if (value && (col.data_type.includes('date') || col.data_type.includes('timestamp'))) {
        formValues[col.column_name] = dayjs(value);
      } else {
        formValues[col.column_name] = value;
      }
    });
    
    form.setFieldsValue(formValues);
  };

  const handleUpdate = async () => {
    if (!editingRecord) return;

    try {
      const values = await form.validateFields();
      const updateData: Record<string, any> = {};
      
      // Convert form values back to API format
      Object.keys(values).forEach((key) => {
        const col = tableInfo?.columns.find((c) => c.column_name === key);
        if (col && (col.data_type.includes('date') || col.data_type.includes('timestamp'))) {
          updateData[key] = values[key] ? values[key].toISOString() : null;
        } else {
          updateData[key] = values[key];
        }
      });
      
      // Exclude system columns
      delete updateData.id;
      delete updateData.created_at;
      delete updateData.updated_at;

      await updateRecord.mutateAsync({
        tableName,
        id: editingRecord.id,
        data: updateData,
      });
      message.success('Registro atualizado com sucesso!');
      setEditingRecord(null);
      form.resetFields();
    } catch (error) {
      // Error já é tratado
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteRecord.mutateAsync({ tableName, id });
      message.success('Registro deletado com sucesso!');
    } catch (error) {
      // Error já é tratado
    }
  };

  const columns: ColumnsType<Record<string, any>> = useMemo(() => {
    if (!tableInfo) return [];

    const systemColumns = ['id', 'created_at', 'updated_at'];
    const editableColumns = tableInfo.columns.filter(
      (col) => !systemColumns.includes(col.column_name)
    );

    const cols: ColumnsType<Record<string, any>> = editableColumns.map((col) => ({
      title: col.column_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      dataIndex: col.column_name,
      key: col.column_name,
      render: (value: any) => {
        if (value === null || value === undefined) return '-';
        if (col.data_type.includes('date') || col.data_type.includes('timestamp')) {
          return formatDateTime(value);
        }
        if (col.data_type.includes('uuid')) {
          return String(value).substring(0, 8) + '...';
        }
        return String(value);
      },
    }));

    // Add system columns
    cols.push({
      title: 'Criado em',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (date ? formatDateTime(date) : '-'),
    });

    // Add actions column
    cols.push({
      title: 'Ações',
      key: 'actions',
      fixed: 'right',
      width: 150,
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
            title="Tem certeza que deseja deletar este registro?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sim"
            cancelText="Não"
          >
            <Button
              icon={<DeleteOutlined />}
              danger
              size="small"
              loading={deleteRecord.isPending}
            >
              Deletar
            </Button>
          </Popconfirm>
        </Space>
      ),
    });

    return cols;
  }, [tableInfo, deleteRecord.isPending]);

  const renderFormField = (col: any) => {
    const fieldName = col.column_name;
    const isRequired = !col.is_nullable && !col.column_default;

    if (col.data_type.includes('uuid')) {
      return (
        <Form.Item
          key={fieldName}
          name={fieldName}
          label={fieldName.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
          rules={isRequired ? [{ required: true }] : []}
        >
          <Input disabled />
        </Form.Item>
      );
    }

    if (col.data_type.includes('int') || col.data_type.includes('numeric') || col.data_type.includes('decimal')) {
      return (
        <Form.Item
          key={fieldName}
          name={fieldName}
          label={fieldName.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
          rules={isRequired ? [{ required: true }] : []}
        >
          <InputNumber style={{ width: '100%' }} />
        </Form.Item>
      );
    }

    if (col.data_type.includes('bool')) {
      return (
        <Form.Item
          key={fieldName}
          name={fieldName}
          label={fieldName.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
          valuePropName="checked"
          rules={isRequired ? [{ required: true }] : []}
        >
          <Select>
            <Select.Option value={true}>Sim</Select.Option>
            <Select.Option value={false}>Não</Select.Option>
          </Select>
        </Form.Item>
      );
    }

    if (col.data_type.includes('date') || col.data_type.includes('timestamp')) {
      return (
        <Form.Item
          key={fieldName}
          name={fieldName}
          label={fieldName.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
          rules={isRequired ? [{ required: true }] : []}
        >
          <DatePicker style={{ width: '100%' }} showTime={col.data_type.includes('timestamp')} />
        </Form.Item>
      );
    }

    return (
      <Form.Item
        key={fieldName}
        name={fieldName}
        label={fieldName.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
        rules={isRequired ? [{ required: true }] : []}
      >
        <Input />
      </Form.Item>
    );
  };

  return (
    <>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        scroll={{ x: 'max-content' }}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} registros`,
          pageSizeOptions: ['10', '20', '50', '100'],
          onChange: (page, size) => {
            if (onPageChange) {
              onPageChange(page, size);
            }
          },
        }}
      />

      <Modal
        title="Editar Registro"
        open={!!editingRecord}
        onOk={handleUpdate}
        onCancel={() => {
          setEditingRecord(null);
          form.resetFields();
        }}
        confirmLoading={updateRecord.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          {tableInfo?.columns
            .filter((col) => !['id', 'created_at', 'updated_at'].includes(col.column_name))
            .map((col) => renderFormField(col))}
        </Form>
      </Modal>
    </>
  );
};
