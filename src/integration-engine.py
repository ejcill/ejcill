#!/usr/bin/env python3
"""
Integration Engine - Orchestrates multiple flows and handles their interactions
"""

import asyncio
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

from flow_manager import FlowManager, Flow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """Execution status for flows and workflows"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

@dataclass
class FlowExecution:
    """Represents a flow execution instance"""
    id: str
    flow_name: str
    flow_version: str
    status: ExecutionStatus
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

@dataclass
class WorkflowDefinition:
    """Defines how multiple flows work together"""
    name: str
    description: str
    flows: List[Dict[str, Any]]
    triggers: List[str] = None
    environment: Dict[str, str] = None
    timeout: Optional[int] = None
    error_handling: Optional[Dict] = None

@dataclass
class WorkflowExecution:
    """Represents a workflow execution instance"""
    id: str
    workflow_name: str
    status: ExecutionStatus
    flow_executions: Dict[str, FlowExecution]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

class IntegrationEngine:
    """Orchestrates multiple flows and manages their interactions"""
    
    def __init__(self, flow_manager: FlowManager, config_dir: str = "config"):
        self.flow_manager = flow_manager
        self.config_dir = Path(config_dir)
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load workflow definitions
        self._load_workflows()
    
    def _load_workflows(self):
        """Load workflow definitions from config files"""
        workflow_file = self.config_dir / "integration-workflows.yaml"
        
        if not workflow_file.exists():
            logger.info("No integration workflows file found, creating example")
            self._create_example_workflows()
            return
        
        try:
            with open(workflow_file, 'r') as f:
                config = yaml.safe_load(f)
                
            for workflow_data in config.get('workflows', []):
                workflow = WorkflowDefinition(**workflow_data)
                self.workflows[workflow.name] = workflow
                logger.info(f"Loaded workflow: {workflow.name}")
                
        except Exception as e:
            logger.error(f"Error loading workflows: {e}")
    
    def _create_example_workflows(self):
        """Create example workflow configuration"""
        example_config = {
            'workflows': [
                {
                    'name': 'complete-data-pipeline',
                    'description': 'End-to-end data processing with validation and reporting',
                    'flows': [
                        {
                            'name': 'data-ingestion-flow',
                            'triggers': ['schedule', 'webhook']
                        },
                        {
                            'name': 'data-processing-flow',
                            'depends_on': ['data-ingestion-flow'],
                            'input_mapping': {
                                'source_data': 'data-ingestion-flow.outputs.raw_data'
                            }
                        },
                        {
                            'name': 'reporting-flow',
                            'depends_on': ['data-processing-flow'],
                            'input_mapping': {
                                'data': 'data-processing-flow.outputs.processed_data'
                            }
                        }
                    ],
                    'timeout': 3600,
                    'error_handling': {
                        'on_failure': 'stop',
                        'notifications': [
                            {
                                'type': 'email',
                                'config': {'recipients': ['admin@example.com']}
                            }
                        ]
                    }
                },
                {
                    'name': 'ci-cd-pipeline',
                    'description': 'Continuous integration and deployment workflow',
                    'flows': [
                        {
                            'name': 'build-flow',
                            'triggers': ['git-push']
                        },
                        {
                            'name': 'test-flow',
                            'depends_on': ['build-flow'],
                            'input_mapping': {
                                'build_artifacts': 'build-flow.outputs.artifacts'
                            }
                        },
                        {
                            'name': 'deploy-flow',
                            'depends_on': ['test-flow'],
                            'condition': 'test-flow.outputs.success == true',
                            'input_mapping': {
                                'artifacts': 'build-flow.outputs.artifacts',
                                'test_results': 'test-flow.outputs.results'
                            }
                        }
                    ]
                }
            ]
        }
        
        workflow_file = self.config_dir / "integration-workflows.yaml"
        with open(workflow_file, 'w') as f:
            yaml.dump(example_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created example workflows at {workflow_file}")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a new workflow definition"""
        # Validate that all referenced flows exist
        for flow_def in workflow.flows:
            flow_name = flow_def['name']
            flow = self.flow_manager.get_flow(flow_name)
            if not flow:
                logger.error(f"Workflow '{workflow.name}' references non-existent flow '{flow_name}'")
                return False
        
        self.workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")
        return True
    
    def get_workflow(self, name: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by name"""
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all registered workflows"""
        return list(self.workflows.values())
    
    async def execute_workflow(self, workflow_name: str, inputs: Dict[str, Any] = None) -> WorkflowExecution:
        """Execute a workflow asynchronously"""
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # Create workflow execution
        execution_id = str(uuid.uuid4())
        workflow_execution = WorkflowExecution(
            id=execution_id,
            workflow_name=workflow_name,
            status=ExecutionStatus.PENDING,
            flow_executions={},
            started_at=datetime.now().isoformat()
        )
        
        self.active_executions[execution_id] = workflow_execution
        
        try:
            # Build execution plan
            execution_plan = self._build_execution_plan(workflow)
            
            # Execute flows according to plan
            workflow_execution.status = ExecutionStatus.RUNNING
            await self._execute_flows(workflow_execution, execution_plan, inputs or {})
            
            workflow_execution.status = ExecutionStatus.COMPLETED
            workflow_execution.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            workflow_execution.status = ExecutionStatus.FAILED
            workflow_execution.error_message = str(e)
            workflow_execution.completed_at = datetime.now().isoformat()
            logger.error(f"Workflow execution failed: {e}")
        
        return workflow_execution
    
    def _build_execution_plan(self, workflow: WorkflowDefinition) -> List[List[str]]:
        """Build execution plan with dependency resolution"""
        flows = {flow_def['name']: flow_def for flow_def in workflow.flows}
        plan = []
        executed = set()
        
        while len(executed) < len(flows):
            # Find flows that can be executed (no unmet dependencies)
            ready_flows = []
            
            for flow_name, flow_def in flows.items():
                if flow_name in executed:
                    continue
                
                dependencies = flow_def.get('depends_on', [])
                if all(dep in executed for dep in dependencies):
                    ready_flows.append(flow_name)
            
            if not ready_flows:
                # Circular dependency or missing dependency
                remaining = set(flows.keys()) - executed
                raise ValueError(f"Cannot resolve dependencies for flows: {remaining}")
            
            plan.append(ready_flows)
            executed.update(ready_flows)
        
        return plan
    
    async def _execute_flows(self, workflow_execution: WorkflowExecution, execution_plan: List[List[str]], inputs: Dict[str, Any]):
        """Execute flows according to the execution plan"""
        workflow = self.get_workflow(workflow_execution.workflow_name)
        flows_config = {flow_def['name']: flow_def for flow_def in workflow.flows}
        
        for parallel_flows in execution_plan:
            # Execute flows in parallel within each stage
            tasks = []
            
            for flow_name in parallel_flows:
                flow_config = flows_config[flow_name]
                task = self._execute_single_flow(workflow_execution, flow_name, flow_config, inputs)
                tasks.append(task)
            
            # Wait for all flows in this stage to complete
            await asyncio.gather(*tasks)
            
            # Check if any flow failed and handle according to error policy
            failed_flows = [
                name for name in parallel_flows
                if workflow_execution.flow_executions[name].status == ExecutionStatus.FAILED
            ]
            
            if failed_flows:
                error_handling = workflow.error_handling or {}
                on_failure = error_handling.get('on_failure', 'stop')
                
                if on_failure == 'stop':
                    raise Exception(f"Flows failed: {failed_flows}")
                elif on_failure == 'continue':
                    logger.warning(f"Continuing despite failed flows: {failed_flows}")
                # Add more error handling strategies as needed
    
    async def _execute_single_flow(self, workflow_execution: WorkflowExecution, flow_name: str, flow_config: Dict, global_inputs: Dict[str, Any]):
        """Execute a single flow within a workflow"""
        # Get the flow definition
        flow = self.flow_manager.get_flow(flow_name)
        if not flow:
            raise ValueError(f"Flow '{flow_name}' not found")
        
        # Create flow execution
        execution_id = str(uuid.uuid4())
        flow_execution = FlowExecution(
            id=execution_id,
            flow_name=flow_name,
            flow_version=flow.version,
            status=ExecutionStatus.PENDING,
            inputs={},
            outputs={},
            started_at=datetime.now().isoformat()
        )
        
        workflow_execution.flow_executions[flow_name] = flow_execution
        
        try:
            # Resolve inputs
            flow_inputs = self._resolve_flow_inputs(flow_config, workflow_execution, global_inputs)
            flow_execution.inputs = flow_inputs
            
            # Check condition if specified
            condition = flow_config.get('condition')
            if condition and not self._evaluate_condition(condition, workflow_execution):
                flow_execution.status = ExecutionStatus.SKIPPED
                flow_execution.completed_at = datetime.now().isoformat()
                logger.info(f"Flow '{flow_name}' skipped due to condition: {condition}")
                return
            
            # Execute the flow
            flow_execution.status = ExecutionStatus.RUNNING
            
            # Simulate flow execution (in a real implementation, this would call the actual flow executor)
            await self._simulate_flow_execution(flow, flow_inputs, flow_execution)
            
            flow_execution.status = ExecutionStatus.COMPLETED
            flow_execution.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            flow_execution.status = ExecutionStatus.FAILED
            flow_execution.error_message = str(e)
            flow_execution.completed_at = datetime.now().isoformat()
            logger.error(f"Flow '{flow_name}' execution failed: {e}")
            raise
    
    def _resolve_flow_inputs(self, flow_config: Dict, workflow_execution: WorkflowExecution, global_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve input mappings for a flow"""
        inputs = {}
        
        # Start with global inputs
        inputs.update(global_inputs)
        
        # Apply input mappings
        input_mapping = flow_config.get('input_mapping', {})
        for input_name, mapping in input_mapping.items():
            value = self._resolve_mapping(mapping, workflow_execution)
            if value is not None:
                inputs[input_name] = value
        
        return inputs
    
    def _resolve_mapping(self, mapping: str, workflow_execution: WorkflowExecution) -> Any:
        """Resolve a mapping expression like 'flow-name.outputs.field'"""
        if not isinstance(mapping, str) or '.' not in mapping:
            return mapping
        
        parts = mapping.split('.')
        if len(parts) < 3:
            return mapping
        
        flow_name, section, field = parts[0], parts[1], '.'.join(parts[2:])
        
        if flow_name not in workflow_execution.flow_executions:
            logger.warning(f"Referenced flow '{flow_name}' not found in execution")
            return None
        
        flow_execution = workflow_execution.flow_executions[flow_name]
        
        if section == 'outputs':
            return flow_execution.outputs.get(field)
        elif section == 'inputs':
            return flow_execution.inputs.get(field)
        
        return None
    
    def _evaluate_condition(self, condition: str, workflow_execution: WorkflowExecution) -> bool:
        """Evaluate a condition expression (simplified implementation)"""
        # This is a simplified condition evaluator
        # In a real implementation, you'd want a proper expression parser
        
        try:
            # Replace flow references with actual values
            for flow_name, flow_execution in workflow_execution.flow_executions.items():
                condition = condition.replace(f"{flow_name}.outputs.", f"flow_outputs['{flow_name}'].")
                condition = condition.replace(f"{flow_name}.inputs.", f"flow_inputs['{flow_name}'].")
            
            # Create evaluation context
            flow_outputs = {name: exec.outputs for name, exec in workflow_execution.flow_executions.items()}
            flow_inputs = {name: exec.inputs for name, exec in workflow_execution.flow_executions.items()}
            
            # Evaluate condition (WARNING: This is unsafe for production use)
            # In production, use a safe expression evaluator
            return eval(condition, {"flow_outputs": flow_outputs, "flow_inputs": flow_inputs})
            
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    async def _simulate_flow_execution(self, flow: Flow, inputs: Dict[str, Any], flow_execution: FlowExecution):
        """Simulate flow execution (placeholder for actual execution logic)"""
        # This is a simulation - in a real implementation, this would:
        # 1. Execute each step in the flow
        # 2. Handle dependencies between steps
        # 3. Manage state and data flow
        # 4. Handle errors and retries
        
        logger.info(f"Executing flow '{flow.name}' with inputs: {inputs}")
        
        # Simulate some processing time
        await asyncio.sleep(1)
        
        # Generate mock outputs based on flow definition
        outputs = {}
        for output_def in flow.outputs or []:
            if output_def.type == "json":
                outputs[output_def.name] = {"processed": True, "timestamp": datetime.now().isoformat()}
            elif output_def.type == "string":
                outputs[output_def.name] = f"result-{uuid.uuid4().hex[:8]}"
            elif output_def.type == "boolean":
                outputs[output_def.name] = True
            else:
                outputs[output_def.name] = f"mock-{output_def.type}-value"
        
        flow_execution.outputs = outputs
        logger.info(f"Flow '{flow.name}' completed with outputs: {outputs}")
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the status of a workflow execution"""
        return self.active_executions.get(execution_id)
    
    def list_active_executions(self) -> List[WorkflowExecution]:
        """List all active workflow executions"""
        return list(self.active_executions.values())
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            return False
        
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.now().isoformat()
        
        # Cancel individual flow executions
        for flow_execution in execution.flow_executions.values():
            if flow_execution.status == ExecutionStatus.RUNNING:
                flow_execution.status = ExecutionStatus.CANCELLED
                flow_execution.completed_at = datetime.now().isoformat()
        
        logger.info(f"Cancelled workflow execution: {execution_id}")
        return True

async def main():
    """Example usage of IntegrationEngine"""
    # Initialize components
    flow_manager = FlowManager()
    flow_manager.discover_flows()
    
    engine = IntegrationEngine(flow_manager)
    
    # List available workflows
    workflows = engine.list_workflows()
    print(f"Available workflows: {[w.name for w in workflows]}")
    
    # Execute a workflow (if any exist)
    if workflows:
        workflow_name = workflows[0].name
        print(f"Executing workflow: {workflow_name}")
        
        execution = await engine.execute_workflow(workflow_name, {"test_input": "example"})
        print(f"Execution completed with status: {execution.status}")
        
        for flow_name, flow_exec in execution.flow_executions.items():
            print(f"  Flow '{flow_name}': {flow_exec.status}")

if __name__ == "__main__":
    asyncio.run(main())
