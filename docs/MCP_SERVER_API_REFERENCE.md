# Sophia AI - MCP Server API Reference

This document lists the core HTTP endpoints exposed by an MCP server. Endpoints are secured with JWT authentication loaded automatically from Pulumi ESC.

## Base URL

```
http://<mcp-server-host>:8002
```

## Endpoints

| Method | Endpoint | Description |
|-------|----------|-------------|
| `GET` | `/health` | Server health check |
| `POST` | `/auth/token` | Obtain JWT token |
| `POST` | `/tools/<name>` | Execute a registered tool |
| `POST` | `/resources/<name>` | Access a resource or query data |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/docs` | Interactive API docs |

### Tool Invocation Example

```bash
curl -X POST http://localhost:8002/tools/gong_call_analysis \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"call_id": "12345"}'
```

### Resource Query Example

```bash
curl -X POST http://localhost:8002/resources/hubspot_contacts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "customer@example.com"}'
```

## Troubleshooting

- **401 Unauthorized** – verify the JWT token from `/auth/token` and ensure the MCP server can access Pulumi ESC.
- **404 Not Found** – confirm the tool or resource name exists in `mcp_config.json` and the corresponding module is loaded.
- **Server Unreachable** – check container logs with `docker-compose -f docker-compose.mcp.yml logs <service>` and restart if necessary.

## Maintenance

1. Update the `mcp_config.json` file when adding tools or resources.
2. Restart the MCP container to apply configuration changes:
   ```bash
   docker-compose -f docker-compose.mcp.yml restart <service>
   ```
3. Review `/metrics` regularly to monitor usage and performance.
