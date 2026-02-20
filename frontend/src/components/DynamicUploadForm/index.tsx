'use client';

import { useState } from 'react';
import { Upload, Button, Steps, message, Card } from 'antd';
import { InboxOutlined, UploadOutlined } from '@ant-design/icons';
import { usePreviewSpreadsheet } from '@/lib/api/hooks/useImportPreview';
import { useCreateJob } from '@/lib/api/hooks/useJobs';
import { SpreadsheetPreview } from '../SpreadsheetPreview';
import { ColumnMapping } from '../ColumnMapping';
import { MappingConfig, ColumnMapping as ColumnMappingType } from '@/lib/types/api';
import { useRouter } from 'next/navigation';

const { Dragger } = Upload;

type Step = 'upload' | 'preview' | 'mapping' | 'complete';

export const DynamicUploadForm: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [mappingConfig, setMappingConfig] = useState<MappingConfig | null>(null);
  
  const previewMutation = usePreviewSpreadsheet();
  const createJob = useCreateJob();
  const router = useRouter();

  const handleFileSelect = async (file: File) => {
    setFile(file);
    setCurrentStep('preview');
    
    try {
      const previewData = await previewMutation.mutateAsync(file);
      setPreview(previewData);
    } catch (error: any) {
      message.error(`Erro ao analisar arquivo: ${error?.response?.data?.detail || error.message}`);
      setCurrentStep('upload');
    }
  };

  const handleMappingComplete = (config: MappingConfig) => {
    setMappingConfig(config);
    setCurrentStep('complete');
  };

  const handleUpload = async () => {
    if (!file || !mappingConfig) {
      message.error('Arquivo e configuração de mapeamento são obrigatórios');
      return;
    }

    // Validate mappingConfig structure
    if (!mappingConfig.target_table || !mappingConfig.target_table.trim()) {
      message.error('Por favor, defina o nome da tabela destino');
      return;
    }

    if (!mappingConfig.columns || mappingConfig.columns.length === 0) {
      message.error('Por favor, mapeie pelo menos uma coluna');
      return;
    }

    // Validate entity fields if creating table
    if (mappingConfig.create_table) {
      if (!mappingConfig.entity_display_name || !mappingConfig.entity_display_name.trim()) {
        message.error('Por favor, defina o nome de exibição da entidade');
        return;
      }
    }

    try {
      const result = await createJob.mutateAsync({ file, mappingConfig });
      message.success('Importação iniciada com sucesso!');
      router.push(`/jobs/${result.job_id}`);
    } catch (error: any) {
      message.error(`Erro ao iniciar importação: ${error?.response?.data?.detail || error.message}`);
    }
  };

  const steps = [
    {
      title: 'Upload',
      content: (
        <Dragger
          accept=".csv,.xlsx,.xls"
          beforeUpload={(file) => {
            handleFileSelect(file);
            return false;
          }}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Clique ou arraste o arquivo aqui</p>
          <p className="ant-upload-hint">Suporte para CSV, XLS e XLSX</p>
        </Dragger>
      ),
    },
    {
      title: 'Preview',
      content: preview ? (
        <SpreadsheetPreview preview={preview} />
      ) : (
        <div>Carregando preview...</div>
      ),
    },
    {
      title: 'Mapeamento',
      content: preview ? (
        <ColumnMapping
          columns={preview.columns}
          mappings={mappingConfig?.columns || []}
          onChange={(mappings) => {
            setMappingConfig({
              target_table: mappingConfig?.target_table || '',
              create_table: mappingConfig?.create_table || false,
              columns: mappings,
              entity_display_name: mappingConfig?.entity_display_name,
              entity_description: mappingConfig?.entity_description,
            });
          }}
          targetTable={mappingConfig?.target_table || ''}
          onTargetTableChange={(table) => {
            setMappingConfig({
              ...mappingConfig!,
              target_table: table,
            });
          }}
          onCreateTableChange={(create) => {
            setMappingConfig({
              ...mappingConfig!,
              create_table: create,
            });
          }}
          createTable={mappingConfig?.create_table || false}
          entityDisplayName={mappingConfig?.entity_display_name}
          onEntityDisplayNameChange={(name) => {
            setMappingConfig({
              ...mappingConfig!,
              entity_display_name: name,
            });
          }}
          entityDescription={mappingConfig?.entity_description}
          onEntityDescriptionChange={(description) => {
            setMappingConfig({
              ...mappingConfig!,
              entity_description: description,
            });
          }}
        />
      ) : null,
    },
  ];

  return (
    <Card>
      <Steps current={currentStep === 'upload' ? 0 : currentStep === 'preview' ? 1 : currentStep === 'mapping' ? 2 : 3} items={steps} />
      
      <div style={{ marginTop: 24 }}>
        {steps[currentStep === 'upload' ? 0 : currentStep === 'preview' ? 1 : currentStep === 'mapping' ? 2 : 0].content}
      </div>

      {currentStep === 'preview' && preview && (
        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Button onClick={() => setCurrentStep('upload')} style={{ marginRight: 8 }}>
            Voltar
          </Button>
          <Button type="primary" onClick={() => {
            // Initialize mappingConfig when going to mapping step
            if (!mappingConfig) {
              setMappingConfig({
                target_table: '',
                create_table: false,
                columns: [],
                entity_display_name: '',
                entity_description: '',
              });
            }
            setCurrentStep('mapping');
          }}>
            Continuar para Mapeamento
          </Button>
        </div>
      )}

      {currentStep === 'mapping' && mappingConfig && (
        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Button onClick={() => setCurrentStep('preview')} style={{ marginRight: 8 }}>
            Voltar
          </Button>
          <Button
            type="primary"
            onClick={() => handleMappingComplete(mappingConfig)}
            disabled={!mappingConfig.target_table || mappingConfig?.columns?.length === 0}
          >
            Finalizar Configuração
          </Button>
        </div>
      )}

      {currentStep === 'complete' && (
        <div style={{ marginTop: 24 }}>
          <Card>
            <h3>Configuração Completa</h3>
            <p>Tabela destino: {mappingConfig?.target_table}</p>
            <p>Colunas mapeadas: {mappingConfig?.columns.length}</p>
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Button onClick={() => setCurrentStep('mapping')} style={{ marginRight: 8 }}>
                Voltar
              </Button>
              <Button type="primary" onClick={handleUpload} loading={createJob.isPending}>
                Iniciar Importação
              </Button>
            </div>
          </Card>
        </div>
      )}
    </Card>
  );
};
