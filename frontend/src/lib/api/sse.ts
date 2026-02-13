/**
 * Server-Sent Events (SSE) client with automatic reconnection
 */

export type SSECallback = (data: any) => void;

export interface SSEClientOptions {
  /** Reconnection delay in milliseconds (default: 1000) */
  reconnectDelay?: number;
  /** Maximum reconnection delay in milliseconds (default: 30000) */
  maxReconnectDelay?: number;
  /** Reconnection backoff multiplier (default: 2) */
  backoffMultiplier?: number;
  /** Maximum number of reconnection attempts (default: Infinity) */
  maxReconnectAttempts?: number;
}

export class SSEClient {
  private eventSource: EventSource | null = null;
  private url: string;
  private options: Required<SSEClientOptions>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private eventHandlers: Map<string, Set<SSECallback>> = new Map();
  private isConnecting = false;
  private isConnected = false;

  constructor(url: string, options: SSEClientOptions = {}) {
    this.url = url;
    this.options = {
      reconnectDelay: options.reconnectDelay ?? 1000,
      maxReconnectDelay: options.maxReconnectDelay ?? 30000,
      backoffMultiplier: options.backoffMultiplier ?? 2,
      maxReconnectAttempts: options.maxReconnectAttempts ?? Infinity,
    };
  }

  /**
   * Connect to the SSE stream
   */
  connect(): void {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    this.isConnecting = true;
    this.eventSource = new EventSource(this.url);

    // Register event listeners for custom events BEFORE setting up handlers
    this.eventHandlers.forEach((callbacks, eventType) => {
      this.eventSource?.addEventListener(eventType, (event: MessageEvent) => {
        try {
          // Skip if no data, empty data, or not a string
          if (!event.data || typeof event.data !== 'string' || event.data.trim() === '') {
            return;
          }
          // Skip SSE comments (lines starting with :)
          if (event.data.trim().startsWith(':')) {
            return;
          }
          const data = JSON.parse(event.data);
          callbacks.forEach((callback) => callback(data));
        } catch (e) {
          // Only log if it's a real error (not empty/comment)
          if (event.data && typeof event.data === 'string' && event.data.trim() !== '' && !event.data.trim().startsWith(':')) {
            console.error('Failed to parse SSE event data:', e, 'Event type:', eventType, 'Data:', event.data);
          }
        }
      });
    });

    // Also listen for 'connected' event from backend
    this.eventSource.addEventListener('connected', (event: MessageEvent) => {
      try {
        // Skip if no data, empty data, or not a string
        if (!event.data || typeof event.data !== 'string' || event.data.trim() === '') {
          return;
        }
        // Skip SSE comments
        if (event.data.trim().startsWith(':')) {
          return;
        }
        const data = JSON.parse(event.data);
        this.emit('connected', data);
      } catch (e) {
        // Only log if it's a real error
        if (event.data && typeof event.data === 'string' && event.data.trim() !== '' && !event.data.trim().startsWith(':')) {
          console.error('Failed to parse connected event:', e, event.data);
        }
      }
    });

    this.eventSource.onopen = () => {
      console.log('SSE connection opened:', this.url);
      this.isConnecting = false;
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.emit('open', {});
    };

    this.eventSource.onerror = (error) => {
      const readyState = this.eventSource?.readyState;
      
      // Only mark as disconnected if connection is actually closed
      if (readyState === EventSource.CLOSED) {
        console.error('SSE connection closed:', this.url);
        this.isConnecting = false;
        this.isConnected = false;
        this.emit('error', error);
        // Attempt reconnection if connection was established before
        this.scheduleReconnect();
      } else if (readyState === EventSource.CONNECTING) {
        // Still connecting, don't treat as error yet
        console.log('SSE still connecting...');
      } else if (readyState === EventSource.OPEN) {
        // Connection is open, this might be a temporary network issue
        // Don't disconnect, just log
        console.warn('SSE connection warning (connection still open)');
      }
    };

    // Listen for message events (default event type)
    this.eventSource.onmessage = (event: MessageEvent) => {
      // Handle default message events (if any)
      if (event.data && typeof event.data === 'string' && event.data.trim() !== '' && !event.data.trim().startsWith(':')) {
        try {
          const data = JSON.parse(event.data);
          this.emit('message', data);
        } catch (e) {
          console.error('Failed to parse SSE message:', e, event.data);
        }
      }
    };
  }

  /**
   * Disconnect from the SSE stream
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    this.isConnecting = false;
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  /**
   * Register an event handler
   */
  on(eventType: string, callback: SSECallback): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(callback);

    // If already connected, add listener to existing EventSource
    if (this.eventSource) {
      this.eventSource.addEventListener(eventType, (event: MessageEvent) => {
        try {
          // Skip if no data, empty data, or not a string
          if (!event.data || typeof event.data !== 'string' || event.data.trim() === '') {
            return;
          }
          // Skip SSE comments
          if (event.data.trim().startsWith(':')) {
            return;
          }
          const data = JSON.parse(event.data);
          callback(data);
        } catch (e) {
          // Only log if it's a real error
          if (event.data && typeof event.data === 'string' && event.data.trim() !== '' && !event.data.trim().startsWith(':')) {
            console.error('Failed to parse SSE event data:', e, 'Event type:', eventType, 'Data:', event.data);
          }
        }
      });
    }
  }

  /**
   * Remove an event handler
   */
  off(eventType: string, callback: SSECallback): void {
    const callbacks = this.eventHandlers.get(eventType);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.eventHandlers.delete(eventType);
      }
    }
  }

  /**
   * Emit an event to all registered handlers
   */
  private emit(eventType: string, data: any): void {
    const callbacks = this.eventHandlers.get(eventType);
    if (callbacks) {
      callbacks.forEach((callback) => callback(data));
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('max_reconnect_attempts', {});
      return;
    }

    const delay = Math.min(
      this.options.reconnectDelay * Math.pow(this.options.backoffMultiplier, this.reconnectAttempts),
      this.options.maxReconnectDelay
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Reconnecting to SSE (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, delay);
  }

  /**
   * Get connection status
   */
  get connected(): boolean {
    return this.isConnected && this.eventSource?.readyState === EventSource.OPEN;
  }

  /**
   * Get ready state
   */
  get readyState(): number {
    return this.eventSource?.readyState ?? EventSource.CLOSED;
  }
}
