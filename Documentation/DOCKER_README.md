# SearchEventsManager - Docker Deployment

This document explains how to run SearchEventsManager using Docker.

## Prerequisites

- **Docker Desktop** installed (FREE for personal use)
  - Download: https://www.docker.com/products/docker-desktop
  - Install and start Docker Desktop

## Quick Start

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
# Copy the example file
cp backend/.env.example .env

# Edit with your API keys
TICKETMASTER_API_KEY=your_api_key_here
TICKETMASTER_API_SECRET=your_api_secret_here
```

### 2. Build and Run

```bash
# Build and start all containers
docker-compose up --build

# Or run in background (detached mode)
docker-compose up --build -d
```

### 3. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs

## Common Commands

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up --build

# Stop and remove all data
docker-compose down -v
```

## Development vs Production

### Development Mode (Current Setup)
- Frontend runs on port 5173 (Vite dev server)
- Backend runs on port 8002
- Hot reload enabled

### Production Mode (Docker)
- Frontend served by Nginx on port 80
- Backend runs on port 8002
- Optimized build
- Nginx proxies API requests

## File Structure

```
SearchEventsManager/
├── docker-compose.yml          # Orchestration config
├── backend/
│   ├── Dockerfile              # Backend container
│   ├── .dockerignore          # Ignore files
│   └── ...
├── frontend/
│   ├── Dockerfile              # Frontend container
│   ├── nginx.conf              # Nginx configuration
│   ├── .dockerignore          # Ignore files
│   └── ...
└── .env                        # Environment variables
```

## Data Persistence

The following data is persisted using Docker volumes:
- `events_manager.db` - SQLite database
- `logs/` - Application logs
- `st_louis_concert_venues.csv` - Venue data

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :80
netstat -ano | findstr :8002

# Stop the containers
docker-compose down
```

### Rebuild Everything
```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi searchevents-backend searchevents-frontend

# Rebuild
docker-compose up --build
```

### View Container Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker logs searchevents-backend -f
docker logs searchevents-frontend -f
```

### Access Container Shell
```bash
# Backend
docker exec -it searchevents-backend /bin/bash

# Frontend
docker exec -it searchevents-frontend /bin/sh
```

## Moving to Another Machine

1. **Option 1: Copy entire project folder**
   ```bash
   # Copy the whole SearchEventsManager folder
   # On new machine:
   cd SearchEventsManager
   docker-compose up --build
   ```

2. **Option 2: Export Docker images**
   ```bash
   # Save images to tar files
   docker save -o backend.tar searchevents-backend
   docker save -o frontend.tar searchevents-frontend
   
   # On new machine:
   docker load -i backend.tar
   docker load -i frontend.tar
   docker-compose up
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TICKETMASTER_API_KEY` | Ticketmaster API key | Yes |
| `TICKETMASTER_API_SECRET` | Ticketmaster API secret | Yes |

## Security Notes

- The `.env` file contains API keys - **do not commit to git**
- Database is stored locally in the project folder
- No external network access required (except for API calls)

## Resources

- Docker Documentation: https://docs.docker.com/
- Docker Compose Documentation: https://docs.docker.com/compose/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- React Documentation: https://react.dev/
