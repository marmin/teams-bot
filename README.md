# Teams Bot (Python + HF LLM + Reminders)

## Features
- Echo: `echo <text>`
- Free text via Hugging Face LLM
- Reminders: `remind in N minutes[: message]`

## Run (Docker)
```bash
docker build -t teams-bot:local .
docker run --rm -p 3978:3978 --name teams-bot \
  --add-host=host.docker.internal:host-gateway \
  -e HUGGINGFACE_API_TOKEN="hf_..." \
  -e HF_MODEL="Qwen/Qwen2.5-7B-Instruct-1M" \
  teams-bot:local