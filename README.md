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

# Here is a more complex workflow

```python
import logging
from dria_workflows import WorkflowBuilder, ConditionBuilder, Operator, Write, GetAll, Read, Push, Edge, Expression, validate_workflow_json


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Give a starting memory as input
    builder = WorkflowBuilder(memory={"topic_1":"Linear Algebra", "topic_2":"CUDA"})

    # Add steps to your workflow
    builder.generative_step(id="create_query", prompt="Write down a search query related to following topics: {{topic_1}} and {{topic_2}}. If any, avoid asking questions asked before: {{history}}", operator=Operator.GENERATION, inputs=[GetAll.new("history", False)], outputs=[Write.new("search_query")])
    builder.generative_step(id="search", prompt="{{search_query}}", operator=Operator.FUNCTION_CALLING, outputs=[Write.new("result"), Push.new("history")])
    builder.generative_step(id="evaluate", prompt="Evaluate if search result is related and high quality to given question by saying Yes or No. Question: {{search_query}} , Search Result: {{result}}. Only output Yes or No and nothing else.", operator=Operator.GENERATION, outputs=[Write.new("is_valid")])

    # Define the flow of your workflow
    flow = [
        Edge(source="create_query", target="search"),
        Edge(source="search", target="evaluate"),
        Edge(source="evaluate", target="_end", condition=ConditionBuilder.build(expected="Yes", target_if_not="create_query", expression=Expression.CONTAINS, input=Read.new("is_valid", True))),
    ]
    builder.flow(flow)

    # Set the return value of your workflow
    builder.set_return_value("result")

    # Build your workflow
    workflow = builder.build()
    validate_workflow_json(workflow.model_dump_json(indent=2, exclude_unset=True, exclude_none=True))

    workflow.save("search_workflow.json")


if __name__ == "__main__":
    main()
```

Detailed docs soon.
[andthattoo](https://x.com/andthatto)
