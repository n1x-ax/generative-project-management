from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Define schemas for API responses
class OrganizationInfo(BaseModel):
    name: str
    industry: str
    members: int

class TeamMember(BaseModel):
    name: str
    role: str
    responsibilities: str

class TeamContext(BaseModel):
    organization: OrganizationInfo
    team_members: List[TeamMember]
    team_context: str

class ProjectContext(BaseModel):
    user_request: str
    description: str
    team_context: str

class PreprocessingOutput(BaseModel):
    team: TeamContext
    project: ProjectContext

class RoadmapStep(BaseModel):
    title: str
    description: str

class ProjectObjective(BaseModel):
    objective: str
    description: str

class KeyPoint(BaseModel):
    key_point: str
    description: str

class DetailedAnalysis(BaseModel):
    summary: str
    roadmap: List[RoadmapStep]

class ProjectDetails(BaseModel):
    title: str
    description: str
    detailed_analyzis: DetailedAnalysis
    draft_plan: str
    objectives: List[ProjectObjective]
    key_points: List[KeyPoint]

class Task(BaseModel):
    task_name: str
    description: str
    assignee: str
    dependencies: List[str] = []
    estimated_hours: int
    status: str = "Not Started"
    priority: str

class EnhancedTask(BaseModel):
    task_id: str
    task_name: str
    description: str
    assignee: str
    dependencies: List[str] = []
    estimated_hours: int
    status: str
    priority: str
    tag: str

class CalendarTask(BaseModel):
    task_id: str
    task_name: str
    assignee: str
    tag: str
    start_date: str
    end_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str 