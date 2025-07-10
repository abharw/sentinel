# Sentinel: AI Governance & Policy Management

Sentinel is a comprehensive AI governance platform that provides policy management, content evaluation, and safety controls for AI applications. It consists of a Rust CLI for policy management and a FastAPI server for content evaluation and safety checks.

## Architecture

Sentinel follows a microservices architecture with clear separation of concerns:

- **Rust CLI** (`core/`): Command-line interface for policy management
- **FastAPI Server** (`server/`): REST API for content evaluation and policy storage
- **Shared Config** (`shared/`): Common configuration and policy definitions
- **MongoDB Atlas**: Cloud database for policy persistence

### Core Components

```
sentinel/
├── core/                 # Rust CLI application
│   ├── src/
│   │   ├── client/      # HTTP client for API communication
│   │   ├── commands/    # CLI command implementations
│   │   ├── models/      # Data structures and serialization
│   │   └── providers/   # AI provider integrations
│   └── tests/           # Integration tests
├── server/              # FastAPI server
│   ├── api/            # REST API endpoints
│   ├── evaluators/     # Content evaluation engines
│   ├── models/         # Database models and schemas
│   └── services/       # Business logic services
├── shared/             # Shared configuration
│   ├── config/         # Environment configuration
│   └── policies/       # Policy templates and examples
└── README.md
```

## Features

### Policy Management
- Create, read, update, and delete policies via CLI
- YAML-based policy definitions
- Policy versioning and metadata tracking
- Flexible condition and action definitions

### Content Evaluation
- Keyword filtering with configurable rules
- Content safety evaluation using AI models
- Semantic similarity analysis
- Performance and efficiency metrics

### AI Provider Integration
- OpenAI API integration
- Extensible provider architecture
- Request/response logging and monitoring
- Policy enforcement at API level

### Database & Storage
- MongoDB Atlas cloud storage
- Async database operations
- Policy persistence with timestamps
- Scalable document-based storage

## Prerequisites

- **Rust** (1.70+): For CLI development and compilation
- **Python** (3.8+): For FastAPI server
- **MongoDB Atlas**: Cloud database account
- **OpenAI API Key**: For content evaluation features

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sentinel
```

### 2. Set Up Environment

Create the environment configuration file:

```bash
cp shared/config/.env.example shared/config/.env
```

Edit `shared/config/.env` with your credentials:

```env
# MongoDB Atlas Connection
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sentinel?retryWrites=true&w=majority

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
```

### 3. Install Dependencies

**Rust CLI:**
```bash
cd core
cargo build
```

**Python Server:**
```bash
cd server
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
cd server
python run_api.py
```

The server will start on `http://localhost:8080` by default.

### CLI Commands

#### Health Check
```bash
sentinel health
```

#### Policy Management

**List all policies:**
```bash
sentinel policy list
```

**Create a new policy:**
```bash
sentinel policy create path/to/policy.yaml
```

**Get policy details:**
```bash
sentinel policy get <policy-id>
```

**Delete a policy:**
```bash
sentinel policy delete <policy-id>
```

#### Content Validation
```bash
sentinel validate path/to/content.json
```

#### System Monitoring
```bash
sentinel monitor --live
```

### Policy Definition Format

Policies are defined in YAML format:

```yaml
id: "content_safety_policy"
name: "Content Safety Policy"
description: "Filters inappropriate content using keyword detection"
severity: "medium"
enabled: true
conditions:
  type: "keyword_filter"
  parameters:
    keywords: ["inappropriate", "spam", "offensive"]
    case_sensitive: false
    match_all: false
actions:
  type: "block"
  parameters:
    reason: "Content contains inappropriate keywords"
    notify_admin: true
    log_violation: true
```

## API Endpoints

### Health Check
- `GET /health` - System health and evaluator status

### Policy Management
- `GET /policies` - List all policies
- `POST /policies` - Create a new policy
- `GET /policies/{id}` - Get specific policy
- `PUT /policies/{id}` - Update policy
- `DELETE /policies/{id}` - Delete policy

### Content Evaluation
- `POST /evaluate` - Evaluate content against policies
- `POST /validate` - Validate content format and structure

## Development

### Project Structure

The project follows a modular architecture:

- **Commands** (`core/src/commands/`): CLI command implementations
- **Client** (`core/src/client/`): HTTP client for API communication
- **Models** (`core/src/models/`): Data structures and serialization
- **Providers** (`core/src/providers/`): AI service integrations

### Adding New Commands

1. Define the command in `core/src/main.rs`
2. Implement the command logic in `core/src/commands/`
3. Add corresponding API endpoints in `server/api/routes/`

### Adding New Evaluators

1. Create evaluator in `server/evaluators/`
2. Register in `server/services/ai_providers/`
3. Update health check endpoint

### Testing

**Rust Integration Tests:**
```bash
cd core
cargo test
```

**API Testing:**
```bash
cd server
python -m pytest tests/
```

**Manual Testing:**
```bash
# Test policy creation
sentinel policy create shared/policies/sample_policy.yaml

# Test policy listing
sentinel policy list

# Test health check
sentinel health
```

## Configuration

### Environment Variables

- `MONGODB_URI`: MongoDB Atlas connection string
- `OPENAI_API_KEY`: OpenAI API key for content evaluation
- `SERVER_HOST`: Server host address (default: 0.0.0.0)
- `SERVER_PORT`: Server port (default: 8080)

### Database Configuration

The system uses MongoDB Atlas for policy storage:
- Database: `sentinel`
- Collection: `policies`
- Indexes: `id` (unique), `name`, `enabled`

## Deployment

### Production Setup

1. **Environment Configuration:**
   - Set production MongoDB Atlas URI
   - Configure OpenAI API key
   - Set appropriate server host/port

2. **Security Considerations:**
   - Use environment variables for sensitive data
   - Implement proper authentication/authorization
   - Enable HTTPS in production
   - Configure firewall rules

3. **Monitoring:**
   - Set up logging aggregation
   - Monitor API response times
   - Track policy evaluation metrics
   - Set up alerts for system health

### Docker Deployment

```dockerfile
# Example Dockerfile for the server
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run_api.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style

- **Rust**: Follow Rust formatting guidelines (`cargo fmt`)
- **Python**: Use Black for formatting, flake8 for linting
- **Documentation**: Update README and add docstrings for new features

## Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in `/docs`
- Review the API documentation at `/docs` when server is running 
