# Dria Workflows

Dria Workflows enables the creation of workflows for Dria Agents.

## Installation

You can install Dria Workflows using pip:
```bash
pip install dria_workflows
````

## Usage Example

Here's a simple example of how to use Dria Workflows:

```python
import logging
from dria_workflows import WorkflowBuilder, Operator, Write, Edge, validate_workflow_json


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    builder = WorkflowBuilder()

    # Add a step to your workflow
    builder.generative_step(id="write_poem", prompt="Write a poem as if you are Kahlil Gibran", operator=Operator.GENERATION, outputs=[Write.new("poem")])
    
    # Define the flow of your workflow
    flow = [Edge(source="write_poem", target="_end")]
    builder.flow(flow)
    
    # Set the return value of your workflow
    builder.set_return_value("poem")
    
    # Build your workflow
    workflow = builder.build()

    # Validate your workflow
    validate_workflow_json(workflow.model_dump_json(indent=2, exclude_unset=True, exclude_none=True))

    # Save workflow
    workflow.save("poem_workflow.json")


if __name__ == "__main__":
    main()
```




