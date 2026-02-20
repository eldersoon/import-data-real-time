'use client';

import { Upload, message, Button, List, Space } from 'antd';
import { InboxOutlined, UploadOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import { useState } from 'react';
import { useCreateJob } from '@/lib/api/hooks/useJobs';
import { useRouter } from 'next/navigation';

const { Dragger } = Upload;

interface UploadResult {
  filename: string;
  jobId?: string;
  status: 'success' | 'error';
  error?: string;
}

export const UploadForm: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const createJob = useCreateJob();
  const router = useRouter();

  const props: UploadProps = {
    name: 'file',
    multiple: true, // Permitir múltiplos arquivos
    accept: '.csv,.xlsx,.xls',
    fileList,
    beforeUpload: (file) => {
      const isValidType = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type) ||
        file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
      
      if (!isValidType) {
        message.error(`${file.name}: Apenas arquivos CSV, XLS ou XLSX são permitidos!`);
        return Upload.LIST_IGNORE;
      }

      const isLt10M = file.size / 1024 / 1024 < 20;
      if (!isLt10M) {
        message.error(`${file.name}: Arquivo deve ser menor que 20MB!`);
        return Upload.LIST_IGNORE;
      }

      return false; // Prevent auto upload
    },
    onChange(info) {
      setFileList(info.fileList);
    },
    onRemove() {
      // Mantém a lista, apenas remove o arquivo específico
    },
  };

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('Por favor, selecione pelo menos um arquivo!');
      return;
    }

    setUploading(true);
    setUploadResults([]);
    const results: UploadResult[] = [];

    // Processar cada arquivo individualmente
    for (let i = 0; i < fileList.length; i++) {
      const fileItem = fileList[i];
      const file = fileItem.originFileObj;
      
      if (!file) {
        results.push({
          filename: fileItem.name,
          status: 'error',
          error: 'Erro ao processar arquivo',
        });
        continue;
      }

      try {
        const result = await createJob.mutateAsync({ file });
        results.push({
          filename: fileItem.name,
          jobId: result.job_id,
          status: 'success',
        });
        message.success(`${fileItem.name} enviado com sucesso!`);
      } catch (error: any) {
        results.push({
          filename: fileItem.name,
          status: 'error',
          error: error?.response?.data?.detail || 'Erro ao enviar arquivo',
        });
      }
    }

    setUploadResults(results);
    setUploading(false);
    setFileList([]);

    // Redirecionar para jobs se pelo menos um foi bem-sucedido
    const successCount = results.filter(r => r.status === 'success').length;
    if (successCount > 0) {
      message.success(`${successCount} arquivo(s) enviado(s) com sucesso!`);
      setTimeout(() => {
        router.push('/jobs');
      }, 1500);
    }
  };

  return (
    <div>
      <Dragger {...props} style={{ marginBottom: 16 }}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Clique ou arraste os arquivos aqui para fazer upload</p>
        <p className="ant-upload-hint">
          Suporte para múltiplos arquivos CSV, XLS e XLSX. Máximo 20MB por arquivo.
          <br />
          Cada arquivo criará um job separado na fila de processamento.
        </p>
      </Dragger>
      
      <Button
        type="primary"
        icon={<UploadOutlined />}
        onClick={handleUpload}
        loading={uploading}
        disabled={fileList.length === 0}
        size="large"
        block
      >
        {uploading ? 'Enviando...' : `Enviar ${fileList.length} Arquivo(s)`}
      </Button>

      {uploadResults.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>Resultado dos Uploads:</h3>
          <List
            dataSource={uploadResults}
            renderItem={(item) => (
              <List.Item>
                <Space>
                  {item.status === 'success' ? (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                  )}
                  <span>{item.filename}</span>
                  {item.status === 'success' && item.jobId && (
                    <Button
                      type="link"
                      size="small"
                      onClick={() => router.push(`/jobs/${item.jobId}`)}
                    >
                      Ver Job
                    </Button>
                  )}
                  {item.status === 'error' && (
                    <span style={{ color: '#ff4d4f', fontSize: 12 }}>{item.error}</span>
                  )}
                </Space>
              </List.Item>
            )}
          />
        </div>
      )}
    </div>
  );
};
