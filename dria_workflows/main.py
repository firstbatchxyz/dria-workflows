from dria_workflows.workflows import WorkflowBuilder, ConditionBuilder, Operator, Write, GetAll, Read, Push, Edge, Expression

def main():
    builder = WorkflowBuilder(memory={"topic_1":"Linear Algebra", "topic_2":"CUDA"})
    builder.generative_step(id="create_query", prompt="Write down a search query related to following topics: {{topic_1}} and {{topic_2}}. If any, avoid asking questions asked before: {{history}}", operator=Operator.GENERATION, inputs=[GetAll.new("history", False)], outputs=[Write.new("search_query")])
    builder.generative_step(id="search", prompt="{{search_query}}", operator=Operator.FUNCTION_CALLING, outputs=[Write.new("result"), Push.new("history")])
    builder.generative_step(id="evaluate", prompt="Evaluate if search result is related and high quality to given question by saying Yes or No. Question: {{search_query}} , Search Result: {{result}}. Only output Yes or No and nothing else.", operator=Operator.GENERATION, outputs=[Write.new("is_valid")])

    flow = [
        Edge(source="create_query", target="search"),
        Edge(source="search", target="evaluate"),
        Edge(source="evaluate", target="_end", condition=ConditionBuilder.build(expected="Yes", target_if_not="create_query", expression=Expression.CONTAINS, input=Read.new("is_valid", True))),
    ]

    builder.flow(flow)
    workflow = builder.build()

if __name__ == "__main__":
    main() 