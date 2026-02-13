'use client';

import { Badge } from 'antd';
import {
  ClockCircleOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { JobStatus } from '@/lib/types/api';

interface StatusBadgeProps {
  status: JobStatus;
}

const statusConfig = {
  pending: {
    color: '#8c8c8c', // cinza
    icon: <ClockCircleOutlined />,
    text: 'Pendente',
  },
  processing: {
    color: '#1890ff', // azul
    icon: <LoadingOutlined spin />,
    text: 'Em Progresso',
  },
  completed: {
    color: '#52c41a', // verde
    icon: <CheckCircleOutlined />,
    text: 'Concluído',
  },
  failed: {
    color: '#ff4d4f', // vermelho
    icon: <CloseCircleOutlined />,
    text: 'Falhou',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config = statusConfig[status];

  return (
    <Badge
      color={config.color}
      text={
        <span style={{ color: config.color, display: 'flex', alignItems: 'center', gap: 4 }}>
          {config.icon}
          {config.text}
        </span>
      }
    />
  );
};
