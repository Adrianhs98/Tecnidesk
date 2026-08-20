# Mac mini M1 Local Embedding Service Setup Guide

This guide documents the configuration required on a dedicated Mac mini M1 running [Ollama](https://ollama.com/) and exposing the `nomic-embed-text-v2-moe:latest` embedding model to TecniDesk via Tailscale Funnel.

---

## 1. Power Management & Sleep Prevention (`pmset`)

To ensure uninterrupted availability as an internal microservice, prevent the Mac mini from entering system sleep while connected to AC power.

Open Terminal on the Mac mini and run:

```bash
# Disable system sleep on AC power
sudo pmset -c sleep 0

# Disable disk sleep on AC power
sudo pmset -c disksleep 0

# (Optional) Allow display to sleep after 10 minutes to save power while keeping system awake
sudo pmset -c displaysleep 10

# Wake on network access (Wake-on-LAN)
sudo pmset -c womp 1

# Restart automatically after a power failure
sudo pmset -c autorestart 1
```

Verify the active power configuration:

```bash
pmset -g custom
```

Ensure `sleep 0` and `disksleep 0` are active under the `AC Power` profile.

---

## 2. Ollama Installation & Model Setup

### 2.1 Install Ollama
Download and install Ollama for macOS from [ollama.com/download](https://ollama.com/download) or via Homebrew:

```bash
brew install --cask ollama
```

### 2.2 Pull the Embedding Model
TecniDesk uses `nomic-embed-text-v2-moe:latest` (768 dimensions, 512 context token limit):

```bash
ollama pull nomic-embed-text-v2-moe:latest
```

Verify that the model was downloaded:

```bash
ollama list
```

### 2.3 Ollama Host Configuration (Optional / Local Network)
By default, Ollama listens on `127.0.0.1:11434`. To allow local network access before Funnel routing:

```bash
# Launchd environment or shell export
export OLLAMA_HOST="0.0.0.0:11434"
```

---

## 3. Tailscale & Tailscale Funnel Setup

[Tailscale Funnel](https://tailscale.com/kb/1223/funnel) exposes the local Ollama HTTP service to your private backend or secure HTTPS tailnet endpoint.

### 3.1 Install and Authenticate Tailscale
Install Tailscale from the Mac App Store or standalone package, and log into your Tailscale network:

```bash
tailscale up
```

### 3.2 Enable Tailscale Funnel for Port 11434
Expose Ollama's default port (11434) securely:

```bash
# Enable Funnel routing for port 11434
tailscale funnel 11434 on
```

Check the status and obtain your Tailnet Funnel URL:

```bash
tailscale funnel status
```

The output will display your public/tailnet HTTPS address, e.g.:
`https://mac-mini.your-tailnet.ts.net`

---

## 4. Health Checks & Verification

### 4.1 Verify Ollama Service Tags
Test reachability from an external machine or the TecniDesk backend host:

```bash
curl -s https://<tailnet-url>/api/tags | jq .
```

Expected output includes `nomic-embed-text-v2-moe:latest` in `models`.

### 4.2 Test Embedding Generation
Send a sample embedding payload using the required `search_document: ` task prefix:

```bash
curl -X POST https://<tailnet-url>/api/embed \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text-v2-moe:latest",
    "input": "search_document: Brand: Apple | Model: iPhone 13 Pro | Symptom: Pantalla no enciende tras impacto"
  }'
```

Expected response format:
```json
{
  "model": "nomic-embed-text-v2-moe:latest",
  "embeddings": [
    [-0.01234, 0.04567, ..., -0.00891]
  ]
}
```
Verify that the output array contains 768 float values.

---

## 5. Backend Configuration

Update your `.env` file in the TecniDesk `backend/` directory:

```env
LOCAL_EMBEDDING_SERVICE_URL="https://mac-mini.your-tailnet.ts.net"
```

For local development where Ollama is running on the same host:
```env
LOCAL_EMBEDDING_SERVICE_URL="http://localhost:11434"
```
