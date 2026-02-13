import { useState, useEffect, useRef } from 'react';
import { SSEClient } from '@/lib/api/sse';
import { ImportJobResponse, JobStatus } from '@/lib/types/api';
import apiClient from '@/lib/api/client';

const SSE_URL = `${apiClient.defaults.baseURL}/imports/stream`;

export const useJobsSSE = (params?: {
  skip?: number;
  limit?: number;
  status?: string;
}) => {
  const [jobs, setJobs] = useState<ImportJobResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const sseClientRef = useRef<SSEClient | null>(null);

  useEffect(() => {
    // Fetch initial jobs list
    const fetchInitialJobs = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<ImportJobResponse[]>('/imports', { params });
        setJobs(response.data);
        setError(null);
      } catch (err: any) {
        setError(err);
        console.error('Failed to fetch initial jobs:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialJobs();

    // Setup SSE connection for all jobs
    const client = new SSEClient(SSE_URL);
    sseClientRef.current = client;

    // Handle job status updates
    client.on('job_status', (data: any) => {
      console.log('Received job_status event (list):', data);
      setJobs((prev) => {
        const jobId = data.job_id || data.id;
        const index = prev.findIndex((j) => j.id === jobId);

        if (index === -1) {
          // New job, add it if it matches filters
          if (!params?.status || data.status === params.status) {
            return [
              {
                id: jobId,
                filename: data.filename || '',
                status: data.status as JobStatus,
                total_rows: data.total_rows,
                processed_rows: data.processed_rows,
                error_rows: data.error_rows,
                started_at: data.started_at,
                finished_at: data.finished_at,
                created_at: data.created_at || new Date().toISOString(),
              },
              ...prev,
            ];
          }
          return prev;
        }

        // Update existing job
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          status: data.status as JobStatus,
          started_at: data.started_at,
          finished_at: data.finished_at,
          // Also update progress if provided
          processed_rows: data.processed_rows ?? updated[index].processed_rows,
          total_rows: data.total_rows ?? updated[index].total_rows,
          error_rows: data.error_rows ?? updated[index].error_rows,
        };
        return updated;
      });
    });

    // Handle progress updates
    client.on('job_progress', (data: any) => {
      console.log('Received job_progress event (list):', data);
      setJobs((prev) => {
        const jobId = data.job_id || data.id;
        const index = prev.findIndex((j) => j.id === jobId);

        if (index === -1) {
          return prev;
        }

        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          processed_rows: data.processed_rows,
          total_rows: data.total_rows,
          error_rows: data.error_rows,
        };
        return updated;
      });
    });

    // Handle job list updates (for all jobs stream)
    client.on('job_list_update', (data: any) => {
      if (data.jobs && Array.isArray(data.jobs)) {
        setJobs(data.jobs);
      }
    });

    // Handle connection events
    client.on('connected', () => {
      console.log('SSE connected for jobs list');
    });

    client.on('error', (err: any) => {
      console.error('SSE error for jobs list:', err);
      setError(new Error('SSE connection error'));
    });

    client.on('max_reconnect_attempts', () => {
      console.error('Max reconnection attempts reached for jobs list');
      setError(new Error('Failed to maintain SSE connection'));
    });

    // Connect
    client.connect();

    // Cleanup on unmount
    return () => {
      client.disconnect();
      sseClientRef.current = null;
    };
  }, [params?.skip, params?.limit, params?.status]);

  return {
    jobs,
    isLoading,
    error,
    refetch: async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<ImportJobResponse[]>('/imports', { params });
        setJobs(response.data);
        setError(null);
      } catch (err: any) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    },
  };
};
