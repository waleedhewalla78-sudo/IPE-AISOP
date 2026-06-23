type MessageCallback = (data: unknown) => void;

export class FeasibilityWebSocket {
  private ws: WebSocket | null = null;
  private url = '';
  private reconnectAttempt = 0;
  private maxReconnectDelay = 30000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private callbacks: MessageCallback[] = [];
  private shouldReconnect = false;

  connect() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const tenantId = payload.tenant_id as string;
      if (!tenantId) return;

      this.url = `ws://localhost:8004/api/v1/feasibility/ws/${tenantId}?token=${token}`;
      this.shouldReconnect = true;
      this.createConnection();
    } catch {
      return;
    }
  }

  private createConnection() {
    this.ws = new WebSocket(this.url);

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event_type === 'ipe.mo.feasibility_scored') {
          this.callbacks.forEach((cb) => cb(msg.data));
        }
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
    };
  }

  private scheduleReconnect() {
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempt),
      this.maxReconnectDelay,
    );
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => this.createConnection(), delay);
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }

  onMessage(callback: MessageCallback) {
    this.callbacks.push(callback);
    return () => {
      this.callbacks = this.callbacks.filter((cb) => cb !== callback);
    };
  }
}
