# PocketMusec Setup Guide - Milestone 3

Complete installation and configuration guide for PocketMusec with all Milestone 3 features.

## Quick Setup with Make

The project includes a comprehensive Makefile that simplifies common development tasks. If you have Make installed, you can use these commands:

```bash
# Complete setup (installs dependencies + initializes database)
make setup

# Start development servers (backend + frontend)
make dev

# View all available commands
make help
```

For a full list of Make commands, see the [Makefile](../Makefile) or run `make help`.

## Prerequisites

### System Requirements
- Python 3.11 or higher
- Node.js 18 or higher
- 8GB RAM minimum (16GB recommended for local mode)
- 10GB free disk space (for local models and image storage)

### Required Software

#### 1. Tesseract OCR
**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr libtesseract-dev
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

Verify installation:
```bash
tesseract --version
```

#### 2. Ollama (Optional - for Local Mode)
**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download from: https://ollama.com/download

Start Ollama service:
```bash
ollama serve
```

Download the Qwen3 8B model (required for local mode):
```bash
ollama pull qwen2.5:8b
```

This will download ~4.7GB. Monitor progress in the terminal.

Verify installation:
```bash
ollama list
```

## Backend Setup

### 1. Install Python Dependencies

Navigate to the project root:
```bash
cd pocket_musec
```

**Using Make:**
```bash
make install-backend
```

**Manual installation:**
```bash
pip install -e .
```

Or using poetry:
```bash
poetry install
```

Or using uv:
```bash
uv pip install -e .
```

### 2. Configure Environment Variables

**Using Make:**
```bash
make check-env
```
This will automatically copy `.env.example` to `.env` if it doesn't exist.

**Manual setup:**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security (IMPORTANT: Change in production!)
JWT_SECRET_KEY=your-secret-key-here-change-in-production

# CORS (adjust for your frontend URL)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Chutes API (required for Cloud mode)
CHUTES_API_KEY=your-chutes-api-key-here

# Ollama Configuration (for Local mode)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:8b

# Image Processing
IMAGE_STORAGE_PATH=./data/images
IMAGE_STORAGE_QUOTA_MB=5120
TESSERACT_CMD=/usr/bin/tesseract

# Database
DATABASE_PATH=./data/pocket_musec.db
```

**Important Notes:**
- `JWT_SECRET_KEY`: Generate a strong random key for production:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- `CHUTES_API_KEY`: Get your API key from https://chutes.ai
- Change `CORS_ORIGINS` to match your frontend URL(s)

### 3. Initialize Database

**Using Make:**
```bash
make db-init
```

**Manual setup:**
```bash
python -c "from backend.repositories.migrations import DatabaseMigrator; m = DatabaseMigrator('./data/pocket_musec.db'); m.migrate()"
```

This creates the database with all required tables for Milestone 3.

**Reset database (WARNING: deletes all data):**
```bash
make db-reset
```

### 4. Start Backend Server

**Using Make:**
```bash
make dev-backend
```

**Manual start:**
```bash
python run_api.py
```

The server will start on `http://localhost:8000`

Verify it's running:
```bash
curl http://localhost:8000/health
```

## Frontend Setup

### 1. Install Node Dependencies

**Using Make:**
```bash
make install-frontend
```

**Manual installation:**
```bash
cd frontend
npm install
```

### 2. Configure Frontend

The frontend is pre-configured to proxy API requests to `http://localhost:8000`.

If you need to change this, edit `frontend/vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Change if needed
      changeOrigin: true,
    },
  },
},
```

### 3. Start Development Server

**Using Make:**
```bash
make dev-frontend
```

Or start both backend and frontend together:
```bash
make dev
```

**Manual start:**
```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

### 4. Build for Production

**Using Make:**
```bash
make build-frontend
```

**Manual build:**
```bash
npm run build
```

The production build will be in `frontend/dist/`

Serve with a static file server:
```bash
npm install -g serve
serve -s dist -l 3000
```

## Verification Steps

### 1. Test Authentication

Navigate to `http://localhost:5173` and log in with:
- Email: `admin@example.com`
- Password: `Admin123` (or whatever you set)

You should see the dashboard.

### 2. Test Image Upload

1. Click "Upload Images" on the dashboard
2. Drag and drop a sheet music image or diagram
3. Wait for OCR and vision AI processing
4. Verify extracted text and analysis appear

### 3. Test Processing Mode Toggle

1. Go to Settings
2. Switch between Cloud and Local modes
3. For Local mode:
   - Ensure Ollama is running: `ollama list`
   - Verify model status shows "Installed"
   - If not installed, click "Download Local Model"

### 4. Demo Mode

PocketMusec runs in single-user demo mode with no authentication required. All features are available immediately without login or user management.

## Troubleshooting

### Tesseract Not Found
```
Error: Tesseract command not found
```

**Solution:** Set `TESSERACT_CMD` in `.env`:
```bash
# Linux/macOS
TESSERACT_CMD=/usr/bin/tesseract

# Windows
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
```

### Ollama Connection Failed
```
Error: Failed to connect to Ollama
```

**Solution:**
1. Ensure Ollama is running: `ollama serve`
2. Verify base URL in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`
3. Test connection: `curl http://localhost:11434/api/tags`

### Model Not Downloaded
```
Error: Model qwen2.5:8b not found
```

**Solution:**
```bash
ollama pull qwen2.5:8b
```

Wait for download to complete (~4.7GB).

### CORS Errors in Browser
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:** Add your frontend URL to `CORS_ORIGINS` in `.env`:
```bash
CORS_ORIGINS=http://localhost:5173
```

Restart the backend server.

### Database Migration Errors
```
Error: Table already exists
```

**Solution:** This usually means the database is already migrated. To start fresh:

**Using Make:**
```bash
make db-reset
```

**Manual reset:**
```bash
rm ./data/pocket_musec.db
python -c "from backend.repositories.migrations import DatabaseMigrator; m = DatabaseMigrator('./data/pocket_musec.db'); m.migrate()"
```

**Warning:** This deletes all data!

### Image Upload Fails
```
Error: Storage quota exceeded
```

**Solution:** Increase quota in `.env`:
```bash
IMAGE_STORAGE_QUOTA_MB=10240  # 10GB
```

Or delete old images to free space.

### JWT Token Errors
```
Error: Invalid token signature
```

**Solution:** Ensure `JWT_SECRET_KEY` is consistent. If you changed it, all existing tokens are invalidated. Users must log in again.

## Production Deployment

### Security Checklist

- [ ] Generate strong `JWT_SECRET_KEY`
- [ ] Use HTTPS (required for production)
- [ ] Set `CORS_ORIGINS` to your production domain only
- [ ] Change default admin password
- [ ] Set up firewall rules (allow only 80/443)
- [ ] Enable rate limiting (already configured)
- [ ] Set up monitoring and logging
- [ ] Regular database backups
- [ ] Keep Tesseract and Ollama updated

### Recommended Stack

**Backend:**
- Gunicorn or Uvicorn with multiple workers
- Nginx reverse proxy
- SSL certificate (Let's Encrypt)

**Frontend:**
- Static file serving via Nginx
- CDN for assets (optional)

**Database:**
- Regular automated backups to S3 or similar
- Consider PostgreSQL for multi-user production environments

**Monitoring:**
- Application logs
- Error tracking (Sentry, etc.)
- Performance monitoring
- Storage quota monitoring

## Development Commands

The project includes a Makefile with convenient commands for common tasks:

### Installation & Setup
- `make setup` - Complete project setup (install deps + init DB)
- `make install` - Install all dependencies
- `make install-backend` - Install Python dependencies
- `make install-frontend` - Install frontend dependencies
- `make check-env` - Check/create .env file

### Development
- `make dev` - Start both backend and frontend servers
- `make dev-backend` - Start backend API server only
- `make dev-frontend` - Start frontend dev server only
- `make dev-desktop` - Run Electron desktop app

### Building
- `make build` - Build both backend and frontend
- `make build-backend` - Build backend executable
- `make build-frontend` - Build frontend for production
- `make dist-desktop` - Create distributable desktop package

### Testing & Quality
- `make test` - Run all tests
- `make test-backend` - Run backend tests
- `make test-integration` - Run integration tests
- `make lint` - Lint all code
- `make format` - Format all code
- `make type-check` - Run type checking
- `make check` - Run all checks (lint + type-check + test)

### Database
- `make db-init` - Initialize database
- `make db-reset` - Reset database (with confirmation)

### Cleanup
- `make clean` - Clean build artifacts
- `make clean-all` - Clean everything including node_modules

### Utilities
- `make logs` - Show recent log files
- `make help` - Show all available commands

See the [Makefile](../Makefile) for the complete list of commands.

## Next Steps

1. **Read the API documentation**: See `docs/API.md` for endpoint details
2. **Explore features**: Try image upload, citations, mode switching
3. **Configure preferences**: Adjust storage quotas, models, etc.
4. **Integrate with lesson generation**: Use images and citations in lessons

## Support

For issues or questions:
- Check troubleshooting section above
- Review error logs in `./logs/`
- See `README.md` for feature documentation
- Check `openspec/changes/implement-milestone3-advanced-features/` for implementation details
