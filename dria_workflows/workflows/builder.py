import logging
from pydantic import Field, ConfigDict, BaseModel
from typing import Optional, List, Union, Dict, Literal, get_args, Type
from .interface import (
    Input,
    Output,
    InputValueType,
    InputValue,
    Task,
    TaskOutput,
    Condition,
    OutputType,
    Expression,
    MessageInput,
)
from .workflow import Workflow, Edge
from .w_types import Operator, Tools
from .tools import ToolBuilder, HttpRequestTool, CustomTool, CustomToolMode
import json
import re


class ConditionBuilder:
    @staticmethod
    def build(
        expected: Union[str, int],
        expression: Expression,
        input: Input,
        target_if_not: str,
    ) -> Condition:
        return Condition(
            expected=str(expected),
            expression=expression,
            input=input.value,
            target_if_not=target_if_not,
        )


class DraftTask(Task):
    required_inputs: Optional[List[str]] = Field(default=None)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    outputs: List[Output] = []

    def add_input(self, input: Input) -> "DraftTask":
        if not self.inputs:
            self.inputs = []
        self.inputs.append(input)
        return self

    def add_output(self, output: Output) -> "DraftTask":
        self.outputs.append(output)
        return self

    def build(self) -> Task:
        # check if we have required inputs
        if self.required_inputs:
            missing_inputs = [
                input_name
                for input_name in self.required_inputs
                if not any(input.value.key == input_name for input in self.inputs)
            ]
            if missing_inputs:
                raise ValueError(
                    f"Missing required inputs: {', '.join(missing_inputs)}"
                )
        # Warning if there are no outputs
        if self.id != "_end":
            if len(self.outputs) == 0:
                logging.debug(
                    "Warning: Task has no outputs defined. Output of this step is not stored anywhere.\n"
                )
            else:
                output_keys = [output.key for output in self.outputs]
                logging.debug(
                    "Task '%s' output keys: %s\n", self.id, ", ".join(output_keys)
                )

        return Task(
            id=self.id,
            name=self.name,
            description=self.description,
            messages=self.messages,
            schema=self.schema,
            inputs=self.inputs,
            operator=self.operator,
            outputs=self.outputs,
        )


class TaskBuilder:
    @classmethod
    def new(
        cls,
        id: str,
        operator: Operator,
        mmap: dict,
        prompt: Optional[str] = None,
        path: Optional[str] = None,
        msg_history: Optional[List[MessageInput]] = None,
        schema: Optional[Type[BaseModel]] = None,
        _inputs: Optional[List[Input]] = None,
        name: str = "Task",
        description: str = "Task Description",
    ) -> DraftTask:
        # if prompt, messages and path is empty, fail
        if prompt is None and path is None:
            raise ValueError("Either prompt or path must be provided")

        if prompt is None:
            prompt = cls._prompt_from_md(path)

        messages = msg_history or []
        messages.append(MessageInput(role="user", content=prompt))

        inputs: list[Input] = []
        # check using reges for variables with double brackets {{}} and extract them as inputs,
        # for instance {{query}} -> query and add them to inputs list
        input_names = cls._extract_inputs(prompt)
        # add inputs using mmap
        for input_name in input_names:
            if _inputs and any(input_name == input.value.key for input in _inputs):
                continue
            if input_name in mmap:
                input_type = mmap[input_name]
                if InputValueType.GET_ALL in input_type:
                    cls._add_input(inputs, input_name, InputValueType.GET_ALL)
                else:
                    cls._add_input(inputs, input_name, InputValueType.READ)

        if id != "_end":
            logging.debug(
                "Prompt has %s input(s): %s", len(input_names), ", ".join(input_names)
            )
        return DraftTask(
            id=id,
            name=name,
            description=description,
            messages=messages,
            schema=schema,
            operator=operator,
            inputs=inputs,
            outputs=[],
            required_inputs=input_names,
        )

    @staticmethod
    def _prompt_from_md(path="./"):
        if path.endswith(".md"):
            with open(path, "r", encoding="utf-8") as file:
                prompt = file.readlines()
        return "".join(prompt)

    @staticmethod
    def _extract_inputs(prompt: str) -> List[str]:
        pattern = r"\{\{(\w+)\}\}"
        matches = re.findall(pattern, prompt)
        return list(set(matches))

    @staticmethod
    def _add_input(inputs: List[Input], key: str, value_type: InputValueType) -> None:
        input_value = InputValue(type=value_type, key=key)
        input_obj = Input(name=key, value=input_value, required=True)
        inputs.append(input_obj)


class WorkflowBuilder:
    def __init__(self, memory=None, **kwargs):
        if memory is None:
            memory = dict()
        memory.update(kwargs)

        # Type Check for memory
        for key, value in memory.items():
            if not isinstance(value, (str, list)):
                raise ValueError(
                    f"Unsupported memory type for key {key}. Supported types are str, and List[str]"
                )
            for item in value:
                # Check if item is either str or dict
                if not isinstance(item, (str, dict)):
                    raise ValueError(
                        f"Unsupported memory type for key {key}. Supported types are str, and List[str]"
                    )

                # If item is dict, check if all keys and values are strings
                if isinstance(item, dict):
                    if not all(
                        isinstance(k, str) and isinstance(v, str)
                        for k, v in item.items()
                    ):
                        raise ValueError(
                            f"Unsupported memory type for key {key}. Supported types are str, and List[str]"
                        )

        self.workflow = Workflow()
        self.workflow.external_memory = memory
        self.tasks: List[Task] = []
        self.steps = []
        self.memory = memory
        # match memory with InputValueType
        self.map = {}
        [self.__mmap(k, v) for k, v in memory.items()]

    def __mmap(self, key, value):
        """
        Map a key to its corresponding InputValueType(s) based on the value type.

        Args:
            key (str): The key in the memory dictionary.
            value (Union[str, List[str]]): The value associated with the key.

        Raises:
            ValueError: If the value type is not supported (i.e., not str or List[str]).

        Note:
            - For List[str] values, it maps to [GET_ALL, PEEK, POP, SIZE] InputValueTypes.
            - For str values, it maps to [READ] InputValueType.
        """
        if isinstance(value, list) and isinstance(value[0], str):
            self.map[key] = [
                InputValueType.GET_ALL,
                InputValueType.PEEK,
                InputValueType.POP,
                InputValueType.SIZE,
            ]
        elif isinstance(value, str):
            self.map[key] = [InputValueType.READ]
        else:
            raise ValueError(
                f"Unsupported memory type for key {key}. Supported types are str, and List[str]"
            )

    def generative_step(
        self,
        operator: Literal[Operator.GENERATION, Operator.FUNCTION_CALLING],
        prompt: Optional[str] = None,
        path: Optional[str] = None,
        msg_history: Optional[List[MessageInput]] = None,
        id: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        inputs=None,
        outputs=None,
    ):
        """
        Add a step that uses LLMs. This can either be generation or function_calling
        """
        if outputs is None:
            outputs = []
        if inputs is None:
            inputs = []
        if prompt is None and path is None:
            raise ValueError("Either prompt or path for an .md file must be provided")
        if operator == Operator.FUNCTION_CALLING and schema is not None:
            raise ValueError("Schema is not supported for FUNCTION_CALLING operator")

        if id is None:
            id = str(len(self.tasks))
        else:
            # Check if the id already exists in the tasks array
            if any(task.id == id for task in self.tasks):
                raise ValueError(f"Task with id '{id}' already exists")

        task = TaskBuilder.new(
            id=id,
            prompt=prompt,
            path=path,
            msg_history=msg_history,
            schema=schema,
            _inputs=inputs,
            operator=operator,
            mmap=self.map,
        )

        for input in inputs:
            task.add_input(input)
        for output in outputs:
            task.add_output(output)
            if output.type == OutputType.PUSH:
                self.__mmap(output.key, [" "])
            elif output.type == OutputType.WRITE:
                self.__mmap(output.key, "")
            else:
                pass

        self.tasks.append(task.build())

    def search_step(
        self,
        search_query: str,
        search_type: Literal["search", "news", "scholar"] = "search",
        lang: Optional[str] = "en",
        n_results: Optional[int] = 5,
        id: Optional[str] = None,
        inputs=None,
        outputs=None,
    ):
        """
        Add a search step to the workflow.

        Args:
            search_query (str): The search query to be used.
            search_type (str): The type of search to be performed. Default is 'search'.
            lang (str): The language of the search query. Default is 'en'.
            n_results (int): The number of search results to be returned. Default is 5.
            id (str): The id of the task. Default is None.
            inputs (List[Input]): The inputs for the task. Default is None.
            outputs (List[Output]): The outputs for the task. Default is None.

        Raises:
            ValueError: If a task with the given id already exists.

        Note:
            This method creates a new task with the SEARCH operator and adds it to the workflow.
            It also updates the internal memory mapping for any new outputs.
        """
        if outputs is None:
            outputs = []
        if inputs is None:
            inputs = []
        if id is None:
            id = str(len(self.tasks))
        else:
            # Check if the id already exists in the tasks array
            if any(task.id == id for task in self.tasks):
                raise ValueError(f"Task with id '{id}' already exists")

        task = TaskBuilder.new(
            id=id,
            prompt=json.dumps({"query": search_query, "search_type": search_type, "lang": lang, "n_results": n_results}),
            _inputs=inputs,
            operator=Operator.SEARCH,
            mmap=self.map,
        )

        for input in inputs:
            task.add_input(input)
        for output in outputs:
            task.add_output(output)
            if output.type == OutputType.PUSH:
                self.__mmap(output.key, [" "])
            elif output.type == OutputType.WRITE:
                self.__mmap(output.key, "")
            else:
                pass

        self.tasks.append(task.build())

    def add_custom_tool(self, tool: Union[CustomTool, HttpRequestTool]):
        """
        Add a custom tool to the workflow.
        """
        custom_tool = ToolBuilder.build(tool)
        self.workflow.config.custom_tools = self.workflow.config.custom_tools or []
        self.workflow.config.custom_tools.append(custom_tool)

    def build(self) -> Workflow:
        """
        Build the workflow.
        """

        for task in self.tasks:
            self.workflow.add_task(task)

        if (
            self.workflow.config.custom_tools
            and any(
                tool.mode_template.mode == CustomToolMode.CUSTOM
                for tool in self.workflow.config.custom_tools
            )
            and any(
                task.operator == Operator.FUNCTION_CALLING
                for task in self.workflow.tasks
            )
        ):
            raise ValueError(
                "Custom tools are not supported with function_calling tasks. Use FUNCTION_CALLING_RAW instead."
            )

        if self.workflow.config.custom_tools:
            self.workflow.config.custom_tools = [
                tool.serialize_model() for tool in self.workflow.config.custom_tools
            ]

        ending_task = TaskBuilder.new(
            id="_end", prompt="", operator=Operator.END, mmap=self.map
        ).build()
        self.workflow.add_task(ending_task)

        # Check if there exist an edge for every task
        task_ids = set(task.id for task in self.tasks)
        edge_sources = set(edge.source for edge in self.steps)
        edge_targets = set(edge.target for edge in self.steps)

        # Check if there's an edge for every task except the ending task
        tasks_without_edges = task_ids - edge_sources - {"_end"}
        if tasks_without_edges:
            raise ValueError(
                f"The following tasks have no outgoing edges: {', '.join(tasks_without_edges)}"
            )

        # Check if all edge targets are valid tasks
        invalid_targets = edge_targets - task_ids - {"_end"}
        if invalid_targets:
            raise ValueError(
                f"The following edge targets are not valid tasks: {', '.join(invalid_targets)}"
            )

        # Ensure the last task (before _end) has an edge to _end
        if self.tasks and self.tasks[-1].id != "_end":
            last_task_id = self.tasks[-1].id
            if not any(
                edge.source == last_task_id and edge.target == "_end"
                for edge in self.steps
            ):
                self.steps.append(Edge(source=last_task_id, target="_end"))

        # Add the steps to the workflow
        for step in self.steps:
            self.workflow.add_step(
                step.source, step.target, step.condition, step.fallback
            )

        if self.workflow.return_value is None:
            # logging.debug out existing outputs
            keys = [output.key for task in self.tasks for output in task.outputs]

            logging.debug(
                "Warning: No return value set for the workflow. Select one of the %s by running set_return_value('key')",
                keys,
            )

        return self.workflow

    def build_to_dict(self) -> Dict:
        """ """
        workflow = self.build()
        return json.loads(
            workflow.model_dump_json(exclude_unset=True, exclude_none=True)
        )

    def flow(self, edges: List[Edge]):
        for edge in edges:
            if not any(task.id == edge.source for task in self.tasks):
                raise ValueError(f"Source task '{edge.source}' not found")
            if edge.target != "_end":
                if not any(task.id == edge.target for task in self.tasks):
                    raise ValueError(f"Target task '{edge.target}' not found")
            self.steps.append(edge)

    def set_return_value(self, key: Union[str, List[str]]):
        """
        Set the return value for the workflow.

        This method sets the return value of the workflow to the specified key.
        The key should correspond to an output key from one of the tasks in the workflow.

        Args:
            key (str): The key of the output to be set as the return value.

        Returns:
            None

        Raises:
            ValueError: If the specified key does not correspond to any output in the workflow tasks.
        """
        # Check if the key exists in any of the task outputs
        if isinstance(key, str):
            key = [key]
        for k in key:
            if not any(
                k in [output.key for output in task.outputs] for task in self.tasks
            ):
                raise ValueError(
                    f"The key '{key}' does not correspond to any output in the workflow tasks."
                )

        to_json = False
        if len(key) == 1:
            input_value = InputValue(type=self.map[key[0]][0], key=key[0])
            if self.map[key[0]][0] == InputValueType.GET_ALL:
                to_json = True
            self.workflow.return_value = TaskOutput(input=input_value, to_json=to_json)
        else:
            input_value = [InputValue(type=self.map[k][0], key=k) for k in key]
            self.workflow.return_value = TaskOutput(input=input_value, to_json=True)

    def set_max_tokens(self, max_tokens: int):
        """
        Set the maximum number of tokens for the workflow.

        Args:
            max_tokens (int): The maximum number of tokens allowed for the workflow.

        Returns:
            WorkflowBuilder: The current WorkflowBuilder instance for method chaining.
        """
        self.workflow.config.max_tokens = max_tokens

    def set_max_steps(self, max_steps: int):
        """
        Set the maximum number of steps for the workflow.

        Args:
            max_steps (int): The maximum number of steps allowed for the workflow.

        Returns:
            WorkflowBuilder: The current WorkflowBuilder instance for method chaining.
        """
        self.workflow.config.max_steps = max_steps

    def set_max_time(self, max_time: int):
        """
        Set the maximum execution time for the workflow.

        Args:
            max_time (int): The maximum execution time allowed for the workflow in seconds.

        Returns:
            WorkflowBuilder: The current WorkflowBuilder instance for method chaining.
        """
        self.workflow.config.max_time = max_time

    def set_tools(self, tools: List[Tools]):
        """
        Set the tools for the workflow.
        """
        for tool in tools:
            if str(tool) not in set(get_args(Tools)):
                raise ValueError(
                    f"Tool '{tool}' is not a valid tool. Choose from: {', '.join(set(get_args(Tools)))}"
                )
        self.workflow.config.tools = tools
