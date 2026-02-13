'use client';

import { useParams } from 'next/navigation';
import { Card, Typography, Progress, Descriptions, List, Tag, Spin, Button, Space } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useJobSSE } from '@/hooks/useJobSSE';
import { formatDateTime, calculateProgress } from '@/lib/utils/formatters';
import { StatusBadge } from '@/components/StatusBadge';
import Link from 'next/link';
import { Statistic, Row, Col } from 'antd';

const { Title } = Typography;

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;
  const { job, isLoading } = useJobSSE(jobId);

  if (isLoading && !job) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!job) {
    return (
      <div>
        <Title level={2}>Job não encontrado</Title>
        <Link href="/jobs">
          <Button icon={<ArrowLeftOutlined />}>Voltar para Jobs</Button>
        </Link>
      </div>
    );
  }

  const progress = calculateProgress(job.processed_rows, job.total_rows);
  const isProcessing = job.status === 'processing' || job.status === 'pending';

  return (
    <div>
      <Link href="/jobs">
        <Button icon={<ArrowLeftOutlined />} style={{ marginBottom: 16 }}>
          Voltar
        </Button>
      </Link>

      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 24 }}>
          <Title level={2} style={{ margin: 0 }}>
            {job.filename}
          </Title>
          <StatusBadge status={job.status} />
        </Space>

        {isProcessing && job.total_rows && (
          <div style={{ marginBottom: 24 }}>
            <Progress
              percent={progress}
              status={job.status === 'failed' ? 'exception' : 'active'}
              format={(percent) => `${job.processed_rows} / ${job.total_rows} (${percent}%)`}
            />
          </div>
        )}

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Statistic
              title="Total de Linhas"
              value={job.total_rows || 0}
              valueStyle={{ fontSize: 24 }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Processadas"
              value={job.processed_rows}
              valueStyle={{ fontSize: 24, color: '#1890ff' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Erros"
              value={job.error_rows}
              valueStyle={{
                fontSize: 24,
                color: job.error_rows > 0 ? '#ff4d4f' : '#52c41a',
              }}
            />
          </Col>
        </Row>

        <Descriptions title="Informações do Job" bordered column={2}>
          <Descriptions.Item label="ID">{job.id}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <StatusBadge status={job.status} />
          </Descriptions.Item>
          <Descriptions.Item label="Criado em">
            {formatDateTime(job.created_at)}
          </Descriptions.Item>
          <Descriptions.Item label="Iniciado em">
            {formatDateTime(job.started_at)}
          </Descriptions.Item>
          <Descriptions.Item label="Finalizado em">
            {formatDateTime(job.finished_at)}
          </Descriptions.Item>
        </Descriptions>

        {job.logs && job.logs.length > 0 && (
          <Card title="Logs" style={{ marginTop: 24 }}>
            <List
              dataSource={job.logs}
              renderItem={(log) => (
                <List.Item>
                  <Space>
                    <Tag
                      color={
                        log.level === 'error'
                          ? 'red'
                          : log.level === 'warning'
                          ? 'orange'
                          : 'blue'
                      }
                    >
                      {log.level.toUpperCase()}
                    </Tag>
                    <span>{log.message}</span>
                    <span style={{ color: '#8c8c8c', fontSize: 12 }}>
                      {formatDateTime(log.created_at)}
                    </span>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        )}
      </Card>
    </div>
  );
}
