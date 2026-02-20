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

// Mapping and Preview types
export interface ColumnInfo {
  name: string;
  suggested_type: string;
  sample_values: any[];
  null_count: number;
  total_count: number;
}

export interface PreviewResponse {
  columns: ColumnInfo[];
  preview_rows: Record<string, any>[];
  total_rows: number;
  total_columns: number;
}

export interface ForeignKeyConfig {
  table: string;
  lookup_column: string;
  on_missing: 'create' | 'ignore' | 'error';
}

export interface ColumnMapping {
  sheet_column: string;
  db_column: string;
  type: 'string' | 'int' | 'float' | 'decimal' | 'date' | 'datetime' | 'boolean' | 'fk';
  required: boolean;
  fk?: ForeignKeyConfig;
}

export interface MappingConfig {
  target_table: string;
  create_table: boolean;
  columns: ColumnMapping[];
  entity_display_name?: string;
  entity_description?: string;
  entity_icon?: string;
}

export interface ImportTemplate {
  id: string;
  name: string;
  target_table: string;
  create_table: boolean;
  mapping_config: MappingConfig;
  created_at: string;
  updated_at: string;
}

// Dynamic Entity types
export interface DynamicEntityResponse {
  id: string;
  table_name: string;
  display_name: string;
  description?: string;
  is_visible: boolean;
  icon?: string;
  created_at: string;
  updated_at: string;
  created_by_job_id?: string;
}

export interface DynamicEntityUpdate {
  display_name?: string;
  description?: string;
  icon?: string;
  is_visible?: boolean;
}

export interface TableColumnInfo {
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  column_default?: string;
  max_length?: number;
}

export interface TableInfoResponse {
  table_name: string;
  schema: string;
  columns: TableColumnInfo[];
  primary_key?: string;
}
