'use client';

import { Inter } from 'next/font/google';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Layout } from 'antd';
import { Navigation } from '@/components/Navigation';
import { antdTheme } from './antd-theme';
import './globals.css';
import 'antd/dist/reset.css';

const inter = Inter({ subsets: ['latin'] });

const { Sider, Content } = Layout;

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    return makeQueryClient();
  } else {
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const queryClient = getQueryClient();

  return (
    <html lang="pt-BR">
      <head>
        <title>Importação de Veículos</title>
      </head>
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          <ConfigProvider theme={antdTheme}>
            <Layout style={{ minHeight: '100vh' }}>
              <Sider width={200} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
                <div style={{ padding: '16px', textAlign: 'center', fontWeight: 'bold' }}>
                  Importação Veículos
                </div>
                <Navigation />
              </Sider>
              <Layout>
                <Content style={{ padding: '24px', background: '#fff' }}>
                  {children}
                </Content>
              </Layout>
            </Layout>
            <ReactQueryDevtools initialIsOpen={false} />
          </ConfigProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
