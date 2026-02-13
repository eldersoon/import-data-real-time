import axios, { AxiosInstance, AxiosError } from 'axios';
import { message } from 'antd';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as { detail?: string };

      switch (status) {
        case 400:
          message.error(data.detail || 'Requisição inválida');
          break;
        case 404:
          message.error(data.detail || 'Recurso não encontrado');
          break;
        case 500:
          message.error(data.detail || 'Erro interno do servidor');
          break;
        default:
          message.error(data.detail || 'Erro ao processar requisição');
      }
    } else if (error.request) {
      message.error('Erro de conexão com o servidor');
    } else {
      message.error('Erro ao processar requisição');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
