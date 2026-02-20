'use client';

import { Card, Typography, Tabs } from 'antd';
import { UploadForm } from '@/components/UploadForm';
import { DynamicUploadForm } from '@/components/DynamicUploadForm';

const { Title, Paragraph } = Typography;

export default function UploadPage() {
  return (
    <div>
      <Title level={2}>Upload de Arquivos</Title>
      <Paragraph>
        Escolha entre importação rápida (veículos) ou importação configurável (qualquer estrutura).
      </Paragraph>
      <Card>
        <Tabs
          items={[
            {
              key: 'quick',
              label: 'Importação Rápida (Veículos)',
              children: (
                <div>
                  <Paragraph>
                    Faça upload de um ou múltiplos arquivos CSV, XLS ou XLSX contendo os dados dos veículos.
                    Cada arquivo criará um job separado na fila de processamento.
                    <br />
                    <strong>Importante:</strong> Os arquivos serão processados sequencialmente (um por vez).
                    O arquivo deve conter as colunas: modelo, placa, ano, valor_fipe.
                  </Paragraph>
                  <UploadForm />
                </div>
              ),
            },
            {
              key: 'configurable',
              label: 'Importação Configurável',
              children: (
                <div>
                  <Paragraph>
                    Configure o mapeamento de colunas dinamicamente. Você pode mapear qualquer estrutura de planilha
                    para qualquer tabela do banco de dados.
                  </Paragraph>
                  <DynamicUploadForm />
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
