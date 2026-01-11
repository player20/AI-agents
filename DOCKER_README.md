# Docker Deployment

## Quick Start

1. **Set your API key**:
   ```bash
   echo "ANTHROPIC_API_KEY=your_key_here" > .env
   ```

2. **Build and run**:
   ```bash
   docker-compose up -d
   ```

3. **Access the platform**:
   Open http://localhost:7860

## Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access container shell
docker-compose exec multi-agent-team bash
```

## Production Deployment

For production, consider:

1. **Use secrets management** instead of .env file
2. **Enable SSL/TLS** with reverse proxy (nginx, Caddy)
3. **Set up monitoring** (Prometheus, Grafana)
4. **Enable database** (uncomment PostgreSQL in docker-compose.yml)
5. **Scale with** Kubernetes or Docker Swarm

## Environment Variables

- `ANTHROPIC_API_KEY` - Required: Your Anthropic API key
- `GRADIO_SERVER_NAME` - Default: 0.0.0.0
- `GRADIO_SERVER_PORT` - Default: 7860
- `DB_PASSWORD` - Optional: PostgreSQL password (if using database)
