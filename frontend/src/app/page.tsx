import { Typography, Card } from 'antd';
import Link from 'next/link';
import { Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

export default function Home() {
  return (
    <div style={{ textAlign: 'center', padding: '50px 20px' }}>
      <Title level={1}>Sistema de Importação de Veículos</Title>
      <Paragraph style={{ fontSize: 16, marginBottom: 30 }}>
        Faça upload de arquivos CSV ou Excel para importar veículos em massa.
        <br />
        O sistema processa os arquivos de forma assíncrona e você pode acompanhar o progresso em tempo real.
      </Paragraph>
      <Link href="/upload">
        <Button type="primary" size="large" icon={<UploadOutlined />}>
          Começar Importação
        </Button>
      </Link>
    </div>
  );
}
