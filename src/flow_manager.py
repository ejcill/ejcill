#!/usr/bin/env python3
"""
Flow Manager - Handles flow registration, validation, and lifecycle management
"""

import json
import yaml
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from jsonschema import validate, ValidationError
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FlowMetadata:
    """Metadata for a flow"""
    name: str
    version: str
    type: str
    description: str
    author: Optional[str] = None
    tags: List[str] = None
    category: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class FlowInput:
    """Flow input parameter definition"""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    validation: Optional[Dict] = None

@dataclass
class FlowOutput:
    """Flow output parameter definition"""
    name: str
    type: str
    description: Optional[str] = None

@dataclass
class FlowStep:
    """Individual step in a flow"""
    name: str
    action: str
    description: Optional[str] = None
    depends_on: List[str] = None
    condition: Optional[str] = None
    retry: Optional[Dict] = None
    timeout: Optional[int] = None
    config: Optional[Dict] = None
    inputs: Optional[Dict] = None
    outputs: Optional[Dict] = None

@dataclass
class Flow:
    """Complete flow definition"""
    name: str
    version: str
    type: str
    description: str
    metadata: Optional[FlowMetadata] = None
    inputs: List[FlowInput] = None
    outputs: List[FlowOutput] = None
    environment: Optional[Dict] = None
    steps: List[FlowStep] = None
    error_handling: Optional[Dict] = None
    monitoring: Optional[Dict] = None

class FlowManager:
    """Manages flow definitions, validation, and registration"""
    
    def __init__(self, flows_dir: str = "flows", schema_path: str = "schemas/flow-schema.json"):
        # Get the project root directory (parent of src)
        project_root = Path(__file__).parent.parent
        self.flows_dir = project_root / flows_dir
        self.schema_path = project_root / schema_path
        self.flows: Dict[str, Flow] = {}
        self.schema = self._load_schema()
        
        # Ensure flows directory exists
        self.flows_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_schema(self) -> Dict:
        """Load the flow validation schema"""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            return {}
    
    def validate_flow(self, flow_data: Dict) -> bool:
        """Validate a flow definition against the schema"""
        if not self.schema:
            logger.warning("No schema loaded, skipping validation")
            return True
            
        try:
            validate(instance=flow_data, schema=self.schema)
            return True
        except ValidationError as e:
            logger.error(f"Flow validation failed: {e.message}")
            return False
    
    def load_flow_from_file(self, file_path: str) -> Optional[Flow]:
        """Load a flow definition from a YAML or JSON file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Flow file not found: {file_path}")
            return None
            
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    flow_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    flow_data = json.load(f)
                else:
                    logger.error(f"Unsupported file format: {file_path.suffix}")
                    return None
                    
            # Validate the flow
            if not self.validate_flow(flow_data):
                return None
                
            # Convert to Flow object
            flow = self._dict_to_flow(flow_data)
            return flow
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing flow file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading flow {file_path}: {e}")
            return None
    
    def _dict_to_flow(self, flow_data: Dict) -> Flow:
        """Convert dictionary to Flow object"""
        # Extract metadata
        metadata_data = flow_data.get('metadata', {})
        metadata = FlowMetadata(
            name=flow_data['name'],
            version=flow_data['version'],
            type=flow_data['type'],
            description=flow_data.get('description', ''),
            author=metadata_data.get('author'),
            tags=metadata_data.get('tags', []),
            category=metadata_data.get('category'),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Extract inputs
        inputs = []
        for input_data in flow_data.get('inputs', []):
            inputs.append(FlowInput(**input_data))
        
        # Extract outputs
        outputs = []
        for output_data in flow_data.get('outputs', []):
            outputs.append(FlowOutput(**output_data))
        
        # Extract steps
        steps = []
        for step_data in flow_data.get('steps', []):
            steps.append(FlowStep(**step_data))
        
        return Flow(
            name=flow_data['name'],
            version=flow_data['version'],
            type=flow_data['type'],
            description=flow_data.get('description', ''),
            metadata=metadata,
            inputs=inputs,
            outputs=outputs,
            environment=flow_data.get('environment'),
            steps=steps,
            error_handling=flow_data.get('error_handling'),
            monitoring=flow_data.get('monitoring')
        )
    
    def register_flow(self, flow: Flow) -> bool:
        """Register a flow in the manager"""
        flow_key = f"{flow.name}:{flow.version}"
        
        if flow_key in self.flows:
            logger.warning(f"Flow {flow_key} already registered, overwriting")
        
        self.flows[flow_key] = flow
        logger.info(f"Registered flow: {flow_key}")
        return True
    
    def get_flow(self, name: str, version: str = None) -> Optional[Flow]:
        """Get a registered flow by name and version"""
        if version:
            flow_key = f"{name}:{version}"
            return self.flows.get(flow_key)
        else:
            # Return the latest version
            matching_flows = [
                (key, flow) for key, flow in self.flows.items()
                if flow.name == name
            ]
            if matching_flows:
                # Sort by version and return the latest
                latest = max(matching_flows, key=lambda x: x[1].version)
                return latest[1]
        return None
    
    def list_flows(self) -> List[Flow]:
        """List all registered flows"""
        return list(self.flows.values())
    
    def discover_flows(self) -> int:
        """Discover and load all flows from the flows directory"""
        count = 0
        
        for file_path in self.flows_dir.rglob("*.yaml"):
            flow = self.load_flow_from_file(file_path)
            if flow:
                self.register_flow(flow)
                count += 1
        
        for file_path in self.flows_dir.rglob("*.yml"):
            flow = self.load_flow_from_file(file_path)
            if flow:
                self.register_flow(flow)
                count += 1
                
        for file_path in self.flows_dir.rglob("*.json"):
            flow = self.load_flow_from_file(file_path)
            if flow:
                self.register_flow(flow)
                count += 1
        
        logger.info(f"Discovered and loaded {count} flows")
        return count
    
    def save_flow(self, flow: Flow, file_path: str = None) -> bool:
        """Save a flow definition to a file"""
        if not file_path:
            file_path = self.flows_dir / f"{flow.name}.yaml"
        else:
            file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert flow to dictionary
            flow_dict = asdict(flow)
            
            # Remove None values and empty lists
            flow_dict = self._clean_dict(flow_dict)
            
            with open(file_path, 'w') as f:
                yaml.dump(flow_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved flow {flow.name} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving flow {flow.name}: {e}")
            return False
    
    def _clean_dict(self, d: Dict) -> Dict:
        """Remove None values and empty lists from dictionary"""
        if not isinstance(d, dict):
            return d
            
        cleaned = {}
        for key, value in d.items():
            if value is None:
                continue
            elif isinstance(value, dict):
                cleaned_value = self._clean_dict(value)
                if cleaned_value:
                    cleaned[key] = cleaned_value
            elif isinstance(value, list):
                if value:  # Only include non-empty lists
                    cleaned[key] = [self._clean_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        
        return cleaned
    
    def get_flow_dependencies(self, flow: Flow) -> List[str]:
        """Get the dependency graph for a flow's steps"""
        dependencies = []
        
        for step in flow.steps or []:
            if step.depends_on:
                dependencies.extend(step.depends_on)
        
        return list(set(dependencies))
    
    def validate_flow_dependencies(self, flow: Flow) -> bool:
        """Validate that all step dependencies exist within the flow"""
        step_names = {step.name for step in flow.steps or []}
        
        for step in flow.steps or []:
            if step.depends_on:
                for dep in step.depends_on:
                    if dep not in step_names:
                        logger.error(f"Step '{step.name}' depends on non-existent step '{dep}'")
                        return False
        
        return True

def main():
    """Example usage of FlowManager"""
    manager = FlowManager()
    
    # Discover flows
    count = manager.discover_flows()
    print(f"Discovered {count} flows")
    
    # List all flows
    flows = manager.list_flows()
    for flow in flows:
        print(f"Flow: {flow.name} v{flow.version} ({flow.type})")

if __name__ == "__main__":
    main()
