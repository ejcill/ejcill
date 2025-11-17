# Getting Started with Multi-Flow Integration

This guide will help you get up and running with the Multi-Flow Integration system quickly.

## Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of YAML configuration files

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/multi-flow-integration.git
   cd multi-flow-integration
   ```

2. **Install Python dependencies:**
   ```bash
   pip install pyyaml jsonschema
   ```

3. **Verify installation:**
   ```bash
   python src/flow-manager.py
   ```

## Quick Start

### 1. Understanding the Architecture

The Multi-Flow Integration system consists of several key components:

- **Flow Manager**: Handles flow definitions and validation
- **Integration Engine**: Orchestrates multiple flows
- **Communication System**: Manages inter-flow messaging
- **GitHub Actions**: Provides CI/CD integration

### 2. Your First Flow

Create a simple flow definition in `flows/my-first-flow.yaml`:

```yaml
name: "hello-world-flow"
version: "1.0"
type: "automation"
description: "A simple hello world flow"

inputs:
  - name: "message"
    type: "string"
    description: "Message to process"
    required: true
    default: "Hello, World!"

outputs:
  - name: "result"
    type: "string"
    description: "Processed message"

steps:
  - name: "process"
    action: "echo-message"
    description: "Echo the input message"
    config:
      prefix: "Processed: "
    inputs:
      text: "message"
```

### 3. Test Your Flow

Validate your flow definition:

```bash
python src/flow-manager.py
```

You should see output indicating your flow was discovered and validated.

### 4. Create a Workflow

Define how multiple flows work together in `config/my-workflow.yaml`:

```yaml
workflows:
  - name: "simple-pipeline"
    description: "A simple two-step pipeline"
    flows:
      - name: "hello-world-flow"
        triggers: ["manual"]
      - name: "hello-world-flow"
        depends_on: ["hello-world-flow"]
        input_mapping:
          message: "hello-world-flow.outputs.result"
```

### 5. Execute Your Workflow

Run the integration engine to execute your workflow:

```bash
cd src
python -c "
import asyncio
from flow_manager import FlowManager
from integration_engine import IntegrationEngine

async def run():
    manager = FlowManager()
    manager.discover_flows()
    
    engine = IntegrationEngine(manager)
    execution = await engine.execute_workflow('simple-pipeline', {'message': 'Hello from Multi-Flow!'})
    
    print(f'Workflow status: {execution.status.value}')
    for flow_name, flow_exec in execution.flow_executions.items():
        print(f'  {flow_name}: {flow_exec.status.value}')

asyncio.run(run())
"
```

## Core Concepts

### Flows

A **flow** is a sequence of steps that process data or perform actions. Each flow:

- Has a unique name and version
- Defines inputs and outputs
- Contains one or more execution steps
- Can have dependencies between steps
- Includes error handling and retry logic

### Workflows

A **workflow** orchestrates multiple flows:

- Defines execution order and dependencies
- Maps outputs from one flow to inputs of another
- Handles conditional execution
- Manages error propagation

### Steps

Each flow consists of **steps** that:

- Perform specific actions (validate, transform, save, etc.)
- Can depend on other steps
- Have configurable retry and timeout behavior
- Can be conditionally executed

## Directory Structure

```
├── flows/                    # Flow definitions
│   ├── examples/            # Example flows
│   └── schemas/             # Validation schemas
├── config/                  # System configuration
│   ├── integration-workflows.yaml
│   └── communication.yaml
├── src/                     # Core system code
│   ├── flow-manager.py      # Flow management
│   ├── integration-engine.py # Workflow orchestration
│   └── ...
├── .github/workflows/       # GitHub Actions
├── docs/                    # Documentation
└── examples/                # Usage examples
```

## Configuration

### Flow Configuration

Flows are defined in YAML files with the following structure:

```yaml
name: "flow-name"
version: "1.0"
type: "data-pipeline"  # or ci-cd, automation, integration, custom
description: "Flow description"

inputs:
  - name: "input-name"
    type: "json"  # string, number, boolean, json, array, file
    required: true

outputs:
  - name: "output-name"
    type: "json"

steps:
  - name: "step-name"
    action: "action-type"
    depends_on: ["previous-step"]
    config:
      # Step-specific configuration
```

### Workflow Configuration

Workflows are defined in `config/integration-workflows.yaml`:

```yaml
workflows:
  - name: "workflow-name"
    description: "Workflow description"
    flows:
      - name: "first-flow"
        triggers: ["schedule", "webhook"]
      - name: "second-flow"
        depends_on: ["first-flow"]
        input_mapping:
          input_field: "first-flow.outputs.output_field"
```

## Environment Variables

The system uses environment variables for configuration:

```bash
# Communication
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export SMTP_SERVER="smtp.example.com"
export SMTP_USERNAME="user@example.com"
export SMTP_PASSWORD="password"

# Security
export JWT_SECRET="your-jwt-secret"
export ENCRYPTION_KEY="your-encryption-key"

# Monitoring
export METRICS_ENDPOINT="http://prometheus:9090"
export TRACING_ENDPOINT="http://jaeger:14268"
```

## GitHub Actions Integration

The system includes GitHub Actions workflows that:

- Validate flow definitions on changes
- Test the integration engine
- Execute workflows on demand
- Generate integration reports

To trigger a workflow execution:

1. Go to the Actions tab in your GitHub repository
2. Select "Multi-Flow Integration Demo"
3. Click "Run workflow"
4. Choose a workflow and provide test data

## Next Steps

1. **Explore Examples**: Check out the example flows in `flows/examples/`
2. **Read the API Reference**: See `docs/api-reference.md` for detailed API documentation
3. **Learn Integration Patterns**: Review `docs/integration-patterns.md` for common use cases
4. **Customize Configuration**: Modify `config/communication.yaml` for your environment

## Troubleshooting

### Common Issues

1. **Flow validation fails**: Check your YAML syntax and ensure all required fields are present
2. **Workflow execution fails**: Verify that all referenced flows exist and dependencies are correct
3. **GitHub Actions fail**: Ensure Python dependencies are correctly specified

### Getting Help

- Check the logs for detailed error messages
- Review the schema files for validation requirements
- Look at the example flows for reference implementations
- Open an issue on GitHub for bugs or feature requests

## Best Practices

1. **Use descriptive names** for flows, steps, and workflows
2. **Include comprehensive descriptions** for all components
3. **Define clear inputs and outputs** with proper types
4. **Handle errors gracefully** with appropriate retry logic
5. **Test flows individually** before integrating them into workflows
6. **Use version control** for all flow and workflow definitions
7. **Monitor execution** and set up appropriate alerts

Happy flowing! 🚀
