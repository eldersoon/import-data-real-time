export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ImportJobResponse {
  id: string;
  filename: string;
  status: JobStatus;
  total_rows: number | null;
  processed_rows: number;
  error_rows: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface JobLogResponse {
  id: string;
  job_id: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  created_at: string;
}

export interface ImportJobDetail extends ImportJobResponse {
  logs: JobLogResponse[];
}

export interface ImportJobCreateResponse {
  job_id: string;
  status: JobStatus;
}

export interface VehicleResponse {
  id: string;
  job_id: string;
  modelo: string;
  placa: string;
  ano: number;
  valor_fipe: number;
  created_at: string;
  updated_at: string;
}

export interface VehicleUpdate {
  modelo?: string;
  valor_fipe?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
}
