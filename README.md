# PocketMusec

AI-powered music lesson planning application aligned with NC Music Standards.

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/chrisnowlin/pocket_musec.git
cd pocket_musec

# Install dependencies
uv install
cd frontend && npm install

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start the application
make dev
```

Visit http://localhost:5173 to access the application.

## Documentation

- **[Developer Setup Guide](docs/DEVELOPER_SETUP.md)** - Complete setup and development guide
- **[API Documentation](docs/API.md)** - Complete API reference
- **[Coding Standards](docs/CODING_STANDARDS.md)** - Required coding conventions (including camelCase standard)
- **[User Guide](docs/USER_GUIDE.md)** - End-user documentation
- **[Teacher Guide](docs/TEACHER_GUIDE.md)** - Guide for educators

## Development

### Code Standards

**All code MUST follow the camelCase naming convention** for properties and API payloads. See [CODING_STANDARDS.md](docs/CODING_STANDARDS.md) for details.

```python
# Backend - Use CamelModel
from backend.api.models import CamelModel

class UserResponse(CamelModel):
    userId: str
    fullName: str
    createdAt: datetime
```

```typescript
// Frontend - Use camelCase
interface User {
  userId: string;
  fullName: string;
  createdAt: string;
}
```

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test
```

### Building for Production

```bash
# Backend
make build

# Frontend
cd frontend && npm run build
```

## Architecture

- **Backend:** FastAPI (Python) with SQLite database
- **Frontend:** React + TypeScript + Vite
- **API Convention:** RESTful with camelCase JSON payloads
- **Database:** SQLite with automatic snake_case to camelCase conversion

## Contributing

1. Read [CODING_STANDARDS.md](docs/CODING_STANDARDS.md)
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow camelCase naming conventions for all properties
4. Write tests for new features
5. Ensure all tests pass: `pytest && npm test`
6. Submit a pull request

## License

Copyright © 2025 PocketMusec. All rights reserved.

## Support

For issues and questions:
- Check the [documentation](docs/)
- Open an issue on GitHub
- Contact the development team
