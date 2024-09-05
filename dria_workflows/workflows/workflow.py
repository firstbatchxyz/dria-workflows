from .interface import *
from typing import Any, Union

class Workflow(BaseModel):
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
            max_steps=50,
            max_time=200,
            tools=["ALL"],
            custom_tool=None,
            max_tokens=None
        )

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def add_step(self, source: str, target: str, condition: Optional[Condition] = None, fallback: Optional[str] = None) -> None:
        edge = Edge(source=source, target=target, condition=condition, fallback=fallback)
        self.steps.append(edge)

    def set_return_value(self, value: TaskOutput) -> None:
        self.return_value = value

    def set_max_iterations(self, value: int) -> None:
        self.config.max_iterations = value

    def set_timeout(self, value: int) -> None:
        self.config.timeout = value

    def set_log_level(self, value: str) -> None:
        self.config.log_level = value

    def set_max_tokens(self, value:int) -> None:
        self.config.max_tokens = value