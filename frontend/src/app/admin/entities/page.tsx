'use client';

import { Typography, Card } from 'antd';
import { EntityManagementTable } from '@/components/EntityManagementTable';

const { Title } = Typography;

export default function AdminEntitiesPage() {
  return (
    <div>
      <Title level={2} style={{ marginBottom: 16 }}>
        Gerenciar Entidades
      </Title>
      <Card>
        <Typography.Paragraph>
          Gerencie as entidades dinâmicas criadas através de importações. Você pode alterar a visibilidade
          no menu lateral e editar os nomes de exibição.
        </Typography.Paragraph>
        <EntityManagementTable />
      </Card>
    </div>
  );
}
