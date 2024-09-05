from pydantic import BaseModel, Field
from typing import Optional, List, Union
from .interface import Input, Output, InputValueType, InputValue, Task, TaskOutput, Condition, Config, OutputType, Expression
from .workflow import Workflow, Edge
from .w_types import Operator
from .io import Read, GetAll, Size, Peek, Pop, INPUTS, OUTPUTS
import os
import re

class ConditionBuilder:
    def build(expected: Union[str, int], expression: Expression, input: Input, target_if_not:str) -> Condition:
        return Condition(expected=expected, expression=expression, input=input.value, target_if_not=target_if_not)

class DraftTask(Task):
    required_inputs: Optional[List[str]] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def add_input(self, input: Input) -> 'DraftTask':
        if not self.inputs:
            self.inputs = []
        self.inputs.append(input)
        return self

    def add_output(self, output:Output) -> 'DraftTask':
        self.outputs.append(output)
        return self

    def build(self) -> Task:
        # check if we have required inputs
        if self.required_inputs:
            missing_inputs = [input_name for input_name in self.required_inputs if not any(input.value.key == input_name for input in self.inputs)]
            if missing_inputs:
                raise ValueError(f"Missing required inputs: {', '.join(missing_inputs)}")
        # Warning if there are no outputs
        if self.id != "_end":
            if len(self.outputs) == 0:
                print("Warning: Task has no outputs defined. Output of this step is not stored anywhere.\n")
            else:
                output_keys = [output.key for output in self.outputs]
                print(f"Task '{self.id}' output keys: {', '.join(output_keys)}\n")

        return Task(
            id=self.id,
            name=self.name,
            description=self.description,
            prompt=self.prompt,
            inputs=self.inputs,
            operator=self.operator,
            outputs=self.outputs
        )
    

class TaskBuilder:
    inputs: List[Input] = []

    @classmethod
    def new(cls, id:str, operator:Operator, mmap:dict, prompt:Optional[str]=None, path: Optional[str]=None, name:str="Task", description:str="Task Description") -> DraftTask:
        # if both prompt and path is empty, fail
        if prompt is None and path is None:
            raise ValueError("Either prompt or path must be provided")

        if prompt is None:
            prompt = cls._prompt_from_md(path)

        builder = cls()
        # check using reges for variables with double brackets {{}} and extract them as inputs, 
        # for instance {{query}} -> query and add them to inputs list
        input_names = cls._extract_inputs(prompt)
        # add inputs using mmap
        for input_name in input_names:
            if input_name in mmap:
                input_type = mmap[input_name]
                if InputValueType.GET_ALL in input_type:
                    builder._add_input(input_name, InputValueType.GET_ALL)
                else:
                    builder._add_input(input_name, InputValueType.READ)

        if id != "_end":
            print(f"Prompt has {len(input_names)} input(s): {', '.join(input_names)}")
        return DraftTask(
            id=id,
            name=name,
            description=description,
            prompt=prompt,
            operator=operator,
            inputs=cls.inputs,
            outputs=[],
            required_inputs=input_names
        )

    @staticmethod
    def _prompt_from_md(path="./"):
        if path.endswith(".md"):
            with open(path, 'r') as file:
                prompt = file.readlines()
        return "".join(prompt)
    
    @staticmethod
    def _extract_inputs(prompt: str) -> List[str]:
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, prompt)
        return list(set(matches))
    
    @classmethod
    def _add_input(cls, key: str, value_type: InputValueType) -> None:
        input_value = InputValue(type=value_type, key=key)
        input_obj = Input(name=key, value=input_value, required=True)
        cls.inputs.append(input_obj)

class WorkflowBuilder:
    def __init__(self, memory={}):
        self.workflow = Workflow()
        self.workflow.external_memory = memory
        self.tasks: List[Task] = []
        self.steps = []
        self.memory = memory
        # match memory with InputValueType
        self.map = {}
        [self.__mmap(k,v) for k,v in memory.items()]
            
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
            self.map[key] = [InputValueType.GET_ALL, InputValueType.PEEK, InputValueType.POP, InputValueType.SIZE]
        elif isinstance(value, str):
            self.map[key] = [InputValueType.READ]
        else:
            raise ValueError(f"Unsupported memory type for key {key}. Supported types are str, and List[str]")
        
    def generative_step(self, prompt:str, operator: Union[Operator.GENERATION, Operator.FUNCTION_CALLING], id: Optional[str] = None, inputs:Optional[List[Input]]=[], outputs:Optional[List[Output]]=[]):
        """
        Add a step that uses LLMs. This can either be generation or function_calling
        """
        if id is None:
            id = str(len(self.tasks))
        else:
        # Check if the id already exists in the tasks array
            if any(task.id == id for task in self.tasks):
                raise ValueError(f"Task with id '{id}' already exists")
            
        task = TaskBuilder.new(id=id, prompt=prompt, operator=operator, mmap=self.map)
        
        for input in inputs:
            task.add_input(input)
        for output in outputs:
            task.add_output(output)
            self.__mmap(output.key, output.value)
        
        self.tasks.append(task.build())

    def search_step(self, search_query:str, id: Optional[str] = None, inputs:Optional[List[Input]]=[], outputs:Optional[List[Output]]=[]):
        """
        Add a search step to the workflow.

        Args:
            search_query (str): The search query to be used.
            id (Optional[str]): The unique identifier for this task. If None, a default id will be assigned.
            inputs (Optional[List[Input]]): List of input parameters for the search task.
            outputs (Optional[List[Output]]): List of output parameters for the search task.

        Raises:
            ValueError: If a task with the given id already exists.

        Note:
            This method creates a new task with the SEARCH operator and adds it to the workflow.
            It also updates the internal memory mapping for any new outputs.
        """
        if id is None:
            id = str(len(self.tasks))
        else:
        # Check if the id already exists in the tasks array
            if any(task.id == id for task in self.tasks):
                raise ValueError(f"Task with id '{id}' already exists")
            
        task = TaskBuilder.new(id=id, prompt=search_query, operator=Operator.SEARCH, mmap=self.map)
        
        for input in inputs:
            task.add_input(input)
        for output in outputs:
            task.add_output(output)
            self.__mmap(output.key, output.value)
        
        self.tasks.append(task.build())

    def build(self) -> Workflow:
        for task in self.tasks:
            self.workflow.add_task(task)
        
        ending_task = TaskBuilder.new(id="_end", prompt="", operator=Operator.END, mmap=self.map).build()
        self.workflow.add_task(ending_task)

        # Check if there exist an edge for every task
        task_ids = set(task.id for task in self.tasks)
        edge_sources = set(edge.source for edge in self.steps)
        edge_targets = set(edge.target for edge in self.steps)

        # Check if there's an edge for every task except the ending task
        tasks_without_edges = task_ids - edge_sources - {"_end"}
        if tasks_without_edges:
            raise ValueError(f"The following tasks have no outgoing edges: {', '.join(tasks_without_edges)}")

        # Check if all edge targets are valid tasks
        invalid_targets = edge_targets - task_ids - {"_end"}
        if invalid_targets:
            raise ValueError(f"The following edge targets are not valid tasks: {', '.join(invalid_targets)}")

        # Ensure the last task (before _end) has an edge to _end
        if self.tasks and self.tasks[-1].id != "_end":
            last_task_id = self.tasks[-1].id
            if not any(edge.source == last_task_id and edge.target == "_end" for edge in self.steps):
                self.steps.append(Edge(source=last_task_id, target="_end"))

        # Add the steps to the workflow
        for step in self.steps:
            self.workflow.add_step(step.source, step.target, step.condition, step.fallback)

        if self.workflow.return_value is None:
            # Print out existing outputs
            keys = [output.key for task in self.tasks for output in task.outputs]

            print(f"Warning: No return value set for the workflow. Select one of the {keys} by running set_return_value('key')")

        return self.workflow

    def flow(self, edges:List[Edge]):
        for edge in edges:
            if not any(task.id == edge.source for task in self.tasks):
                raise ValueError(f"Source task '{edge.source}' not found")
            if edge.target != "_end":
                if not any(task.id == edge.target for task in self.tasks):
                    raise ValueError(f"Target task '{edge.target}' not found")
            self.steps.append(edge)

    def set_return_value(self, key: str):
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
        if not any(key in [output.key for output in task.outputs] for task in self.tasks):
            raise ValueError(f"The key '{key}' does not correspond to any output in the workflow tasks.")

        input_value = InputValue(type=self.map[key][0], key=key)
        self.workflow.return_value = TaskOutput(input=input_value)

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




