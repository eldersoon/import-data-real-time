'use client';

import { Typography, Card, message } from 'antd';
import { EntityTable } from '@/components/EntityTable';
import { useEntityData, useEntity } from '@/lib/api/hooks/useEntities';
import { useState } from 'react';
import { useParams } from 'next/navigation';

const { Title } = Typography;

export default function EntityPage() {
  const params = useParams();
  const tableName = params.table_name as string;
  
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 10,
  });

  const { data: entity } = useEntity(tableName);
  const { data, isLoading, refetch } = useEntityData(tableName, filters);

  const handlePageChange = (page: number, pageSize: number) => {
    setFilters((prev) => ({
      ...prev,
      page,
      page_size: pageSize,
    }));
  };

  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        {entity?.display_name || tableName}
      </Title>
      {entity?.description && (
        <Card style={{ marginBottom: 16 }}>
          <Typography.Text>{entity.description}</Typography.Text>
        </Card>
      )}

      <EntityTable
        tableName={tableName}
        data={data?.data || []}
        loading={isLoading}
        total={data?.total || 0}
        page={filters.page}
        pageSize={filters.page_size}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
