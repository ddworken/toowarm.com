# Deployment Information

## Architecture

The toowarm.com application is deployed using Docker Compose with Caddy as a reverse proxy.

## Deployment Location

- **Infrastructure directory**: `/root/code/infra/`
- **Application directory**: `/root/code/toowarm.com/`
- **Configuration files**:
  - `docker-compose.yml` - Located in `/root/code/infra/`
  - `Caddyfile` - Located in `/root/code/infra/`

## Service Configuration

### Docker Compose Service
```yaml
toowarm:
  image: python:3.11-slim
  working_dir: /app
  volumes:
    - ../toowarm.com:/app
  ports:
    - 8080:5001
  restart: always
  command: sh -c "pip install -r requirements.txt && python3 app.py"
```

- **Container name**: `infra-toowarm-1`
- **Host port**: 8080
- **Container port**: 5001
- **Volume mount**: Application directory is mounted as a volume, so code changes are live

### Caddy Reverse Proxy
```
ice.dworken.com {
    reverse_proxy localhost:8080
    tls david@daviddworken.com
}
```

- **Domain**: https://ice.dworken.com
- **Proxy target**: localhost:8080
- **TLS**: Automatic HTTPS via Let's Encrypt

## Deployment Commands

### Restart the service
```bash
cd /root/code/infra && docker compose restart toowarm
```

### View logs
```bash
cd /root/code/infra && docker compose logs toowarm
```

### Rebuild and restart
```bash
cd /root/code/infra && docker compose up -d --force-recreate toowarm
```

### Check service status
```bash
cd /root/code/infra && docker compose ps toowarm
```

## Application Startup

The application starts via:
1. `pip install -r requirements.txt` - Installs dependencies
2. `python3 app.py` - Runs the Flask application on port 5001

## Notes

- Code changes to templates and Python files are reflected immediately due to Flask's debug mode and volume mounting
- The service automatically restarts on system reboot (`restart: always`)
- No separate build step required for deployment
