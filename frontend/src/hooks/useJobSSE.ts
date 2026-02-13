import { useState, useEffect, useRef } from 'react';
import { SSEClient } from '@/lib/api/sse';
import { ImportJobDetail, JobStatus } from '@/lib/types/api';
import apiClient from '@/lib/api/client';

const SSE_URL = `${apiClient.defaults.baseURL}/imports/stream`;

export const useJobSSE = (jobId: string) => {
  const [job, setJob] = useState<ImportJobDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const sseClientRef = useRef<SSEClient | null>(null);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    // Fetch initial job data
    const fetchInitialJob = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<ImportJobDetail>(`/imports/${jobId}`);
        setJob(response.data);
        setError(null);
      } catch (err: any) {
        setError(err);
        console.error('Failed to fetch initial job:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialJob();

    // Setup SSE connection
    const url = `${SSE_URL}?job_id=${jobId}`;
    const client = new SSEClient(url);
    sseClientRef.current = client;

    // Handle job status updates
    client.on('job_status', (data: any) => {
      console.log('Received job_status event:', data);
      setJob((prev) => {
        const jobId = data.id || data.job_id;
        // If no previous job or IDs don't match, use the full data
        if (!prev || prev.id !== jobId) {
          // If we have full job data, use it
          if (data.id && data.filename) {
            return data as ImportJobDetail;
          }
          return prev;
        }
        return {
          ...prev,
          status: data.status as JobStatus,
          started_at: data.started_at,
          finished_at: data.finished_at,
        };
      });
    });

    // Handle progress updates
    client.on('job_progress', (data: any) => {
      console.log('Received job_progress event:', data);
      setJob((prev) => {
        const jobId = data.job_id || data.id;
        if (!prev || prev.id !== jobId) {
          return prev;
        }
        return {
          ...prev,
          processed_rows: data.processed_rows,
          total_rows: data.total_rows,
          error_rows: data.error_rows,
        };
      });
    });

    // Handle log updates
    client.on('job_log', (data: any) => {
      setJob((prev) => {
        if (!prev || prev.id !== data.job_id) {
          return prev;
        }
        const newLog = {
          id: data.log_id || Date.now().toString(),
          job_id: data.job_id,
          level: data.level,
          message: data.message,
          created_at: data.created_at || new Date().toISOString(),
        };
        return {
          ...prev,
          logs: [...(prev.logs || []), newLog],
        };
      });
    });

    // Handle connection events
    client.on('connected', () => {
      console.log('SSE connected for job:', jobId);
    });

    client.on('error', (err: any) => {
      console.error('SSE error for job:', jobId, err);
      setError(new Error('SSE connection error'));
    });

    client.on('max_reconnect_attempts', () => {
      console.error('Max reconnection attempts reached for job:', jobId);
      setError(new Error('Failed to maintain SSE connection'));
    });

    // Connect
    client.connect();

    // Cleanup on unmount
    return () => {
      client.disconnect();
      sseClientRef.current = null;
    };
  }, [jobId]);

  return {
    job,
    isLoading,
    error,
    refetch: async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<ImportJobDetail>(`/imports/${jobId}`);
        setJob(response.data);
        setError(null);
      } catch (err: any) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    },
  };
};
