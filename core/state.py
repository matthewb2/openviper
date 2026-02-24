from enum import Enum
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    WAITING_USER = "waiting_user"
    ERROR = "error"


@dataclass
class Task:
    id: str
    description: str
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None


@dataclass
class AgentStateData:
    current_state: AgentState = AgentState.IDLE
    current_task: Task | None = None
    task_history: list[Task] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    max_iterations: int = 10
    last_error: str | None = None

    def add_task(self, task: Task):
        self.current_task = task
        self.task_history.append(task)

    def update_state(self, new_state: AgentState):
        self.current_state = new_state

    def increment_iteration(self):
        self.iteration += 1

    def is_max_iterations_reached(self) -> bool:
        return self.iteration >= self.max_iterations
