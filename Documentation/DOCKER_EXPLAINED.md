# Docker Setup Explained

Let me explain each file and how Docker works with your application.

---

## 1. What is Docker?

Think of Docker as a **shipping container for software**:

```
Traditional Way:
Your Laptop → Install Python → Install Node.js → Install Playwright → Run App

Docker Way:
Your Laptop → Run Container (Everything pre-installed inside)
```

**Analogy**: Instead of furnishing an empty apartment every time you move, you live in a mobile home that's already furnished. Just drive it to the new location!

---

## 2. The Files Explained

### A. `docker-compose.yml` - The Conductor

This is the **main configuration file** that tells Docker:
- What containers to run
- How they connect to each other
- What ports to use

```yaml
services:
  backend:           # Your FastAPI application
    ports: "8002:8002"  # Host:Container
    volumes: ...     # Save database outside container
  
  frontend:          # Your React application
    ports: "80:80"   # Access via browser on port 80
    depends_on: backend  # Start backend first
```

**Think of it as**: A blueprint that shows how to build and connect your services.

---

### B. `backend/Dockerfile` - Backend Recipe

This tells Docker **how to build** your Python backend:

```dockerfile
FROM python:3.11-slim        # Start with Python 3.11
WORKDIR /app                  # Set working directory
COPY requirements.txt .       # Copy dependencies list
RUN pip install -r requirements.txt  # Install Python packages
RUN playwright install chromium      # Install browser for scraping
COPY . .                      # Copy all your code
CMD ["python", "-m", "uvicorn", "main:app", ...]  # Start server
```

**What happens**:
1. Docker downloads a Python image (like downloading Windows)
2. Installs all your requirements (FastAPI, Playwright, etc.)
3. Copies your code into the container
4. Sets the startup command

---

### C. `frontend/Dockerfile` - Frontend Recipe

This builds your React app and serves it with Nginx:

```dockerfile
# Stage 1: Build
FROM node:18-alpine as build
RUN npm install              # Install npm packages
RUN npm run build            # Create production build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html  # Copy built files
CMD ["nginx"]                # Start web server
```

**Two stages**:
1. **Build stage**: Compiles your React code into static files (HTML, CSS, JS)
2. **Serve stage**: Nginx serves those files (like Apache or IIS)

**Why Nginx?**
- Faster than Node.js for serving static files
- Production-ready web server
- Can proxy API requests to backend

---

### D. `frontend/nginx.conf` - Traffic Controller

Nginx needs to know:
- How to serve your React pages
- Where to send API requests

```nginx
# User visits: http://localhost/
location / {
    # Serve React app
    try_files $uri /index.html;
}

# Frontend calls: http://localhost/ticketmaster/search
location /ticketmaster/ {
    # Forward to backend container
    proxy_pass http://backend:8002/ticketmaster/;
}
```

**What it does**:
- `/` → Shows your React UI
- `/ticketmaster/` → Forwards to FastAPI backend
- `/venues/` → Forwards to FastAPI backend
- `/my-events/` → Forwards to FastAPI backend

---

### E. `.dockerignore` - What NOT to Include

Like `.gitignore`, but for Docker builds:

```
venv/           # Virtual environment (Docker creates its own)
node_modules/   # npm packages (Docker installs fresh)
*.pyc           # Compiled Python files
__pycache__/    # Python cache
```

**Why?**
- Reduces build time
- Smaller image size
- Avoids conflicts

---

## 3. How It All Works Together

### Step-by-Step Flow:

```
1. You run: docker-compose up --build

2. Docker reads docker-compose.yml

3. Builds Backend Container:
   - Downloads Python 3.11
   - Installs FastAPI, Playwright, etc.
   - Copies your backend code
   - Sets up to run on port 8002

4. Builds Frontend Container:
   - Downloads Node.js 18
   - Runs npm install
   - Runs npm run build → Creates dist/ folder
   - Downloads Nginx
   - Copies dist/ to Nginx folder
   - Sets up to run on port 80

5. Creates Network:
   - Connects both containers
   - They can talk to each other
   - "backend" hostname → backend container IP

6. Starts Both Containers:
   - Backend: http://localhost:8002
   - Frontend: http://localhost (port 80)

7. User Visits http://localhost:
   - Nginx serves React UI
   - React makes API calls to /ticketmaster/
   - Nginx proxies to backend:8002
   - Backend responds with data
   - React displays events
```

---

## 4. Key Concepts

### Container vs Image

**Image** = Blueprint (like a class in programming)
**Container** = Running instance (like an object)

```bash
# Image
Dockerfile → Build → Image (searchevents-backend:latest)

# Container
Image → Run → Container (searchevents-backend)
```

### Volumes

Your data lives **outside** the container:

```yaml
volumes:
  - ./backend/events_manager.db:/app/events_manager.db
```

**Host path**: `./backend/events_manager.db`  
**Container path**: `/app/events_manager.db`

**Why?**
- Container can be deleted/recreated
- Database stays safe on your host machine
- Like saving files to an external hard drive

### Networking

Containers talk via **service names**:

```yaml
services:
  backend:        # ← This becomes the hostname
    ...
```

Frontend → `http://backend:8002` → Backend Container

**Not** `localhost:8002` because inside Docker, `localhost` refers to the container itself, not the host machine.

---

## 5. Why This is Better

### Before Docker:
```bash
# On your laptop
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install
npm install
npm run dev
# ... and repeat on every machine
```

### With Docker:
```bash
# On any machine with Docker
docker-compose up
# Done! Everything is pre-configured
```

### Benefits:

1. **Consistency**
   - "Works on my machine" → Gone forever
   - Same environment everywhere

2. **Isolation**
   - Won't conflict with other projects
   - Each project has its own Python/Node versions

3. **Portability**
   - Copy folder to new machine
   - Run `docker-compose up`
   - Works immediately

4. **Easy Cleanup**
   - Delete container → Fresh start
   - No leftover packages or configs

---

## 6. Development vs Docker

### Current Development Workflow:
```
start.bat → Opens 2 windows:
  - Backend: venv\Scripts\python -m uvicorn ...
  - Frontend: npm run dev
```

### Docker Workflow:
```
docker-compose up → Runs in background:
  - Backend container (port 8002)
  - Frontend container (port 80)
```

**Difference**: Docker packages everything into containers, but the code is the same!

---

## 7. Moving to Another Machine

### Option 1: Full Project (Recommended)
```
1. Copy SearchEventsManager/ folder
2. Install Docker Desktop
3. Run: docker-compose up --build
```

### Option 2: Export Images
```bash
# Save images to files
docker save -o images.tar searchevents-backend searchevents-frontend

# Copy files to new machine
docker load -i images.tar
docker-compose up
```

---

## Summary

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates all containers |
| `Dockerfile (backend)` | Builds Python backend |
| `Dockerfile (frontend)` | Builds React app + Nginx |
| `nginx.conf` | Routes traffic between frontend/backend |
| `.dockerignore` | Excludes unnecessary files |
| `.env` | Your API keys (not in git) |

**Result**: One command (`docker-compose up`) runs your entire application anywhere!
