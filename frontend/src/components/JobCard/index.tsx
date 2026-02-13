'use client';

import { Card, Progress, Statistic, Row, Col, Space } from 'antd';
import { StatusBadge } from '../StatusBadge';
import { ImportJobResponse } from '@/lib/types/api';
import { formatDateTime, calculateProgress } from '@/lib/utils/formatters';
import Link from 'next/link';

interface JobCardProps {
  job: ImportJobResponse;
}

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const progress = calculateProgress(job.processed_rows, job.total_rows);
  const isProcessing = job.status === 'processing' || job.status === 'pending';

  return (
    <Link href={`/jobs/${job.id}`}>
      <Card
        hoverable
        style={{ marginBottom: 16 }}
        title={
          <Space>
            <span>{job.filename}</span>
            <StatusBadge status={job.status} />
          </Space>
        }
      >
        {isProcessing && job.total_rows && (
          <div style={{ marginBottom: 16 }}>
            <Progress
              percent={progress}
              status={job.status === 'failed' ? 'exception' : 'active'}
              format={(percent) => `${job.processed_rows} / ${job.total_rows}`}
            />
          </div>
        )}

        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="Total de Linhas"
              value={job.total_rows || 0}
              valueStyle={{ fontSize: 16 }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Processadas"
              value={job.processed_rows}
              valueStyle={{ fontSize: 16, color: '#1890ff' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Erros"
              value={job.error_rows}
              valueStyle={{ fontSize: 16, color: job.error_rows > 0 ? '#ff4d4f' : undefined }}
            />
          </Col>
        </Row>

        <div style={{ marginTop: 16, fontSize: 12, color: '#8c8c8c' }}>
          <div>Criado em: {formatDateTime(job.created_at)}</div>
          {job.started_at && <div>Iniciado em: {formatDateTime(job.started_at)}</div>}
          {job.finished_at && <div>Finalizado em: {formatDateTime(job.finished_at)}</div>}
        </div>
      </Card>
    </Link>
  );
};
