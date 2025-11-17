# Multi-Flow Integration Support

A flexible system for integrating multiple core flows to create complex, automated processes. This system allows different types of workflows to communicate, share data, and coordinate their execution seamlessly.

## 🚀 Features

- **Flow Definition System**: Define flows using simple YAML/JSON configuration
- **Integration Engine**: Orchestrate multiple flows with dependency management
- **Inter-Flow Communication**: Event-driven messaging and data sharing between flows
- **GitHub Actions Integration**: Native support for CI/CD workflows
- **Extensible Architecture**: Plugin-based system for custom flow types
- **State Management**: Persistent state tracking across flow executions
- **Error Handling**: Robust error recovery and retry mechanisms

## 🏗️ Architecture

The system is built around several core components:

1. **Flow Manager**: Handles flow registration, validation, and lifecycle management
2. **Integration Engine**: Orchestrates flow execution and manages dependencies
3. **Communication System**: Enables inter-flow messaging and data exchange
4. **State Manager**: Maintains execution state and provides persistence
5. **GitHub Actions Bridge**: Integrates with GitHub's workflow system

## 📋 Quick Start

### 1. Define a Flow

Create a flow configuration in the `flows/` directory:

```yaml
# flows/example-flow.yaml
name: "data-processing-flow"
version: "1.0"
type: "data-pipeline"
description: "Process and transform data from multiple sources"

inputs:
  - name: "source_data"
    type: "json"
    required: true

outputs:
  - name: "processed_data"
    type: "json"

steps:
  - name: "validate"
    action: "validate-data"
    config:
      schema: "schemas/data-schema.json"
  
  - name: "transform"
    action: "transform-data"
    depends_on: ["validate"]
    config:
      transformations:
        - type: "normalize"
        - type: "enrich"

  - name: "output"
    action: "save-data"
    depends_on: ["transform"]
    config:
      destination: "processed/"
```

### 2. Create Integration Workflows

Define how multiple flows work together:

```yaml
# config/integration-workflows.yaml
workflows:
  - name: "complete-data-pipeline"
    description: "End-to-end data processing with validation and reporting"
    flows:
      - name: "data-ingestion-flow"
        triggers: ["schedule", "webhook"]
      - name: "data-processing-flow"
        depends_on: ["data-ingestion-flow"]
        input_mapping:
          source_data: "data-ingestion-flow.outputs.raw_data"
      - name: "reporting-flow"
        depends_on: ["data-processing-flow"]
        input_mapping:
          data: "data-processing-flow.outputs.processed_data"
```

### 3. Execute Flows

```bash
# Run a single flow
python src/flow-executor.py --flow flows/example-flow.yaml

# Run an integration workflow
python src/integration-engine.py --workflow complete-data-pipeline
```

## 📁 Project Structure

```
├── README.md
├── flows/                    # Flow definitions
│   ├── examples/            # Example flows
│   └── schemas/             # Flow validation schemas
├── config/                  # System configuration
│   ├── integration-workflows.yaml
│   └── communication.yaml
├── src/                     # Core system code
│   ├── core/               # Core components
│   ├── messaging/          # Inter-flow communication
│   ├── flow-manager.py     # Flow lifecycle management
│   ├── integration-engine.py # Flow orchestration
│   ├── flow-executor.py    # Individual flow execution
│   ├── state-manager.py    # State persistence
│   └── data-bridge.py      # Data transformation
├── .github/workflows/      # GitHub Actions integration
├── docs/                   # Documentation
├── examples/               # Usage examples
└── tests/                  # Test suites
```

## 🔧 Configuration

The system uses YAML configuration files for maximum flexibility:

- `config/integration-workflows.yaml`: Define multi-flow workflows
- `config/communication.yaml`: Configure inter-flow messaging
- `flows/*.yaml`: Individual flow definitions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your flow types or integrations
4. Submit a pull request

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Flow Configuration](docs/flow-configuration.md)
- [Integration Patterns](docs/integration-patterns.md)

## 🎯 Use Cases

- **CI/CD Pipelines**: Coordinate build, test, and deployment flows
- **Data Processing**: Chain data ingestion, transformation, and analysis
- **Content Management**: Automate content creation, review, and publishing
- **Infrastructure Management**: Orchestrate provisioning, monitoring, and scaling
- **Business Process Automation**: Integrate various business workflows

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
