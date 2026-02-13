'use client';

import { Card, Typography } from 'antd';
import { UploadForm } from '@/components/UploadForm';

const { Title, Paragraph } = Typography;

export default function UploadPage() {
  return (
    <div>
      <Title level={2}>Upload de Arquivos</Title>
      <Paragraph>
        Faça upload de um ou múltiplos arquivos CSV, XLS ou XLSX contendo os dados dos veículos.
        Cada arquivo criará um job separado na fila de processamento.
        <br />
        <strong>Importante:</strong> Os arquivos serão processados sequencialmente (um por vez).
        O arquivo deve conter as colunas: modelo, placa, ano, valor_fipe.
      </Paragraph>
      <Card>
        <UploadForm />
      </Card>
    </div>
  );
}
