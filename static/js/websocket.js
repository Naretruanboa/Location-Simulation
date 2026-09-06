export class Connection {
  constructor(onMessage, onStatus) {
    this.onMessage = onMessage;
    this.onStatus = onStatus;
    this.delay = 500;
    this.open();
  }
  open() {
    this.socket = new WebSocket(
      `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws`,
    );
    this.socket.onopen = () => {
      this.delay = 500;
      this.onStatus(true);
    };
    this.socket.onmessage = (event) => {
      try {
        this.onMessage(JSON.parse(event.data));
      } catch (error) {
        console.error(error);
      }
    };
    this.socket.onclose = () => {
      this.onStatus(false);
      setTimeout(() => this.open(), this.delay);
      this.delay = Math.min(this.delay * 2, 8000);
    };
    this.socket.onerror = () => this.socket.close();
  }
  send(message) {
    if (this.socket.readyState !== WebSocket.OPEN) return false;
    this.socket.send(JSON.stringify(message));
    return true;
  }
}
