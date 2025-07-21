# Clean Architecture

A production-ready FastAPI backend template implementing Clean Architecture principles with modern Python best practices.

## 🏗️ Architecture

This template follows **Clean Architecture** (also known as Hexagonal Architecture) principles, ensuring separation of concerns and maintainability:

```
src/
├── domain/          # Business entities and domain logic
├── app/             # Application layer (use cases, services)
│   ├── use_case/    # Business use cases
│   ├── services/    # Application services
│   └── repositories/ # Repository interfaces
├── adapter/         # Infrastructure adapters
│   ├── repositories/ # Database implementations
│   └── services/    # External service implementations
└── api/             # Web layer (FastAPI routes, middleware)
    └── routes/      # API endpoints
```

## 🚀 Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Clean Architecture** - Separation of concerns with clear layer boundaries
- **SQLModel/SQLAlchemy** - Type-safe ORM with async support
- **PostgreSQL** - Production-ready database with async connections
- **Redis** - Caching and session storage
- **Unit of Work Pattern** - Transaction management
- **Repository Pattern** - Data access abstraction
- **Dependency Injection** - Loose coupling and testability
- **Pydantic** - Data validation and serialization
- **Comprehensive Logging** - Structured logging with correlation IDs
- **Error Handling** - Centralized error management
- **Sentry Integration** - Error tracking and performance monitoring
- **CORS Support** - Cross-origin resource sharing
- **Environment Configuration** - YAML-based configuration management

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd backend-template
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure environment:**
   ```bash
   cp example.env.yaml env.yaml
   ```

4. **Update configuration:**
   Edit `env.yaml` with your settings:
   ```yaml
   DB_URI: "postgresql+asyncpg://username:password@localhost:5432/database"
   MIGRATION_DB_URI: "postgresql://username:password@localhost:5432/database"
   REDIS_URL: "redis://:@localhost:6379/0"
   CORS_ORIGINS: ["http://localhost:3000"]
   API_PORT: "8000"
   SENTRY_ENVIRONMENT: "development"
   ```

5. **Set up database:**
   ```bash
   # Create your PostgreSQL database
   createdb your_database_name
   
   # Run migrations (you'll need to add migration tools)
   # alembic upgrade head
   ```

## 🚦 Running the Application

### Development
```bash
uv run api.py
```

### Production
```bash
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## 🏛️ Architecture Layers

### Domain Layer (`src/domain/`)
Contains business entities and core business logic:
- **Entities:** Core business objects (e.g., `User`)
- **Value Objects:** Immutable objects representing descriptive aspects
- **Domain Services:** Business logic that doesn't fit in entities

### Application Layer (`src/app/`)
Contains application-specific business rules:
- **Use Cases:** Application business rules and orchestration
- **Services:** Application services (caching, unit of work)
- **Repository Interfaces:** Data access contracts

### Adapter Layer (`src/adapter/`)
Contains implementations of interfaces defined in inner layers:
- **Repository Implementations:** Database-specific implementations
- **External Services:** Third-party service integrations

### API Layer (`src/api/`)
Contains web framework-specific code:
- **Routes:** FastAPI endpoints
- **Middleware:** Request/response processing
- **Error Handlers:** HTTP error management

## 📝 Adding New Features

### 1. Define Domain Entity
```python
# src/domain/product.py
from sqlmodel import Field
from .base import BaseModel, generate_uuid
from datetime import datetime

class Product(BaseModel, table=True):
    __tablename__ = "products"
    
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(max_length=255)
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2. Create Repository Interface
```python
# src/app/repositories/product_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.product import Product

class ProductRepository(ABC):
    @abstractmethod
    async def save(self, product: Product) -> Product:
        pass
    
    @abstractmethod
    async def find_by_id(self, product_id: str) -> Optional[Product]:
        pass
```

### 3. Implement Repository
```python
# src/adapter/repositories/product_repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.repositories.product_repository import ProductRepository
from src.domain.product import Product

class SQLProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product
```

### 4. Create Use Case
```python
# src/app/use_case/create_product.py
from pydantic import BaseModel
from src.domain.product import Product
from src.app.services.unit_of_work import UnitOfWork
from libs.result import Result, Return

class CreateProductCommand(BaseModel):
    name: str
    price: float

class CreateProductUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work
    
    async def execute(self, command: CreateProductCommand) -> Result:
        async with self.unit_of_work as uow:
            product = Product(name=command.name, price=command.price)
            saved_product = await uow.product_repository.save(product)
            await uow.commit()
            return Return.ok(saved_product)
```

### 5. Add API Route
```python
# src/api/routes/product.py
from fastapi import APIRouter, Depends
from src.app.use_case.create_product import CreateProductUseCase, CreateProductCommand
from src.depends import get_create_product_use_case

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/")
async def create_product(
    command: CreateProductCommand,
    use_case: CreateProductUseCase = Depends(get_create_product_use_case)
):
    result = await use_case.execute(command)
    return result.unwrap()
```

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src
```

## 🔧 Configuration

Configuration is managed through `env.yaml`. Available settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `DB_URI` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `API_PORT` | API server port | 8000 |
| `API_HOST` | API server host | 0.0.0.0 |
| `LOG_LEVEL` | Logging level | INFO |
| `CORS_ORIGINS` | Allowed CORS origins | [] |
| `ENABLE_SENTRY` | Enable Sentry monitoring | 0 |
| `DSN_SENTRY` | Sentry DSN | - |

## 📊 Monitoring & Logging

- **Structured Logging:** JSON-formatted logs with correlation IDs
- **Sentry Integration:** Error tracking and performance monitoring
- **Health Check Endpoint:** `/health` for monitoring systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the architecture patterns
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
