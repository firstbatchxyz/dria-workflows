from .interface import *
from typing import Any, Union


class Workflow(BaseModel):
    """
    Workflow class that represents a workflow.
    
    Args:
        config (Config, optional): The configuration of the workflow. Defaults to None.
        external_memory (Optional[Dict[str, Union[str, StackPage]], optional): The external memory of the workflow. Defaults to None.
        tasks (List[Task], optional): The tasks of the workflow. Defaults to [].
        steps (List[Edge], optional): The steps of the workflow. Defaults to [].
        return_value (Optional[TaskOutput], optional): The return value of the workflow. Defaults to None.
    """
    config: Config
    external_memory: Optional[Dict[str, Union[str, StackPage]]] = None
    tasks: List[Task] = []
    steps: List[Edge] = []
    return_value: Optional[TaskOutput] = None

    def __init__(self, config: Optional[Config] = None):
        config = config or self.default_config()
        super().__init__(config=config)
        self.tasks = []
        self.steps = []
        self.external_memory = {}
        self.return_value = None

    @staticmethod
    def default_config() -> Config:
        return Config(
            max_steps=50, max_time=200, tools=["ALL"], custom_tools=None, max_tokens=None
        )

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def add_step(
        self,
        source: str,
        target: str,
        condition: Optional[Condition] = None,
        fallback: Optional[str] = None,
    ) -> None:
        edge = Edge(
            source=source, target=target, condition=condition, fallback=fallback
        )
        self.steps.append(edge)

    def save(self, file_path: str) -> None:
        """
        Save the workflow as a JSON file.

        Args:
            file_path (str): The path where the JSON file will be saved.
        """
        import json

        workflow_dict = self.model_dump(exclude_unset=True, exclude_none=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(workflow_dict, f, indent=2)
