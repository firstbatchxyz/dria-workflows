import pytest
from dria_workflows import (
    WorkflowBuilder,
    Operator,
    Write,
    Edge,
    Read,
    GetAll,
    ConditionBuilder,
    Expression,
    Push,
    validate_workflow_json,
)


def test_workflow_builder():
    builder = WorkflowBuilder()

    # Add a step to the workflow
    builder.generative_step(
        id="write_poem",
        prompt="Write a poem as if you are Kahlil Gibran",
        operator=Operator.GENERATION,
        outputs=[Write.new("poem")],
    )

    # Define the flow of the workflow
    flow = [Edge(source="write_poem", target="_end")]
    builder.flow(flow)

    # Set the return value of the workflow
    builder.set_return_value("poem")

    # Build the workflow
    workflow = builder.build()

    # Validate the workflow
    json_data = workflow.model_dump_json(
        indent=2, exclude_unset=True, exclude_none=True
    )
    assert validate_workflow_json(json_data)

    # Check if the task was added correctly
    assert len(workflow.tasks) == 2  # Including the _end task
    assert workflow.tasks[0].id == "write_poem"
    assert workflow.tasks[0].operator == Operator.GENERATION
    assert workflow.tasks[0].prompt == "Write a poem as if you are Kahlil Gibran"

    # Check if the flow was set correctly
    assert len(workflow.steps) == 1
    assert workflow.steps[0].source == "write_poem"
    assert workflow.steps[0].target == "_end"

    # Check if the return value was set correctly
    assert workflow.return_value.input.key == "poem"
    assert workflow.return_value.input.type == "read"

    # Check if the config was set with default values
    assert workflow.config.max_steps == 50
    assert workflow.config.max_time == 200
    assert workflow.config.tools == ["ALL"]


def test_complex_workflow_builder():
    # Initialize the WorkflowBuilder with memory
    builder = WorkflowBuilder(memory={"topic_1": "Linear Algebra", "topic_2": "CUDA"})

    # Add steps to the workflow
    builder.generative_step(
        id="create_query",
        prompt="Write down a search query related to following topics: {{topic_1}} and {{topic_2}}. If any, avoid asking questions asked before: {{history}}",
        operator=Operator.GENERATION,
        inputs=[GetAll.new("history", False)],
        outputs=[Write.new("search_query")],
    )
    builder.generative_step(
        id="search",
        prompt="{{search_query}}",
        operator=Operator.FUNCTION_CALLING,
        outputs=[Write.new("result"), Push.new("history")],
    )
    builder.generative_step(
        id="evaluate",
        prompt="Evaluate if search result is related and high quality to given question by saying Yes or No. Question: {{search_query}} , Search Result: {{result}}. Only output Yes or No and nothing else.",
        operator=Operator.GENERATION,
        outputs=[Write.new("is_valid")],
    )

    # Define the flow of the workflow
    flow = [
        Edge(source="create_query", target="search"),
        Edge(source="search", target="evaluate"),
        Edge(
            source="evaluate",
            target="_end",
            condition=ConditionBuilder.build(
                expected="Yes",
                target_if_not="create_query",
                expression=Expression.CONTAINS,
                input=Read.new("is_valid", True),
            ),
        ),
    ]
    builder.flow(flow)

    # Set the return value of the workflow
    builder.set_return_value("result")

    # Build the workflow
    workflow = builder.build()

    # Validate the workflow
    json_data = workflow.model_dump_json(
        indent=2, exclude_unset=True, exclude_none=True
    )
    assert validate_workflow_json(json_data)
