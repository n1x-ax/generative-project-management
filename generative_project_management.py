import json
import datetime
import os
import pathlib
import logging
from pydantic import BaseModel, TypeAdapter
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generative_pm.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GenProjectManagement")

# Load environment variables from .env file if present
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Path to prompts directory
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"

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

def safe_format(template, replacement_dict):
    """
    Safely format a string template with replacement values.
    
    Args:
        template (str): Template string with {placeholders}
        replacement_dict (dict): Dictionary of replacements where keys are the placeholders
            and values are the replacement values
    
    Returns:
        str: Formatted string with replacements
    """
    if not isinstance(template, str):
        logger.warning("Template is not a string, returning as is")
        return template
        
    if not isinstance(replacement_dict, dict):
        logger.warning("Replacement dict is not a dictionary, returning template as is")
        return template
        
    result = template
    for placeholder, value in replacement_dict.items():
        if not isinstance(placeholder, str):
            logger.warning(f"Placeholder {placeholder} is not a string, skipping")
            continue
            
        if value is None:
            value = ""
        elif not isinstance(value, str):
            value = str(value)
            
        result = result.replace(placeholder, value)
    
    return result

def log_parsed_json(step_name, response_json, parsed_model=None):
    """Helper function to log parsed JSON for debugging"""
    try:
        if parsed_model:
            logger.info(f"JSON validation successful for {step_name}")
            logger.debug(f"{step_name} parsed model: {parsed_model.model_dump_json()}")
        else:
            # Truncate the response for logging but ensure it's valid JSON first
            try:
                if isinstance(response_json, str):
                    # Test if it's valid JSON
                    try:
                        json.loads(response_json)
                        is_valid = True
                    except json.JSONDecodeError:
                        is_valid = False
                        
                    if not is_valid:
                        logger.error(f"Invalid JSON in {step_name} response. First 100 chars: {response_json[:100]}...")
                        return
                        
                # Now that we know it's valid or already parsed, log it
                if isinstance(response_json, str):
                    truncated = response_json[:200] + "..." if len(response_json) > 200 else response_json
                else:
                    truncated_json = json.dumps(response_json)
                    truncated = truncated_json[:200] + "..." if len(truncated_json) > 200 else truncated_json
                    
                logger.info(f"JSON response for {step_name}: {truncated}")
            except Exception as e:
                logger.error(f"Error processing JSON in {step_name}: {str(e)}")
                logger.error(f"First 100 chars of response: {str(response_json)[:100]}...")
    except Exception as e:
        logger.error(f"Error logging JSON for {step_name}: {str(e)}")
        if isinstance(response_json, str):
            logger.error(f"Response content preview: {response_json[:100]}...")

def load_prompt(filename):
    """Load a prompt from a text file in the prompts directory."""
    logger.debug(f"Loading prompt from {filename}")
    with open(PROMPTS_DIR / filename, 'r') as f:
        return f.read()

# Load prompts from files
system_prompt = load_prompt("system_prompt.txt")
preprocessing_system_prompt = load_prompt("preprocessing_prompt.txt")
project_details_prompt = load_prompt("project_details_prompt.txt")
tasks_prompt = load_prompt("tasks_prompt.txt")
calendar_prompt = load_prompt("calendar_prompt.txt")

def preprocessing(user_input, team_context):
    """
    Preprocess user input and team context to extract structured data for project planning.
    
    Args:
        user_input (str): The user's project request
        team_context (dict): Information about the team and organization
        
    Returns:
        str: JSON string with preprocessed data
    """
    logger.info("Step 1: Starting preprocessing")
    
    # Join user input and team context into a single JSON object
    combined_input = {
        "user_input": user_input,
        "team_context": team_context
    }
    
    # Convert to string if input is a dictionary
    if isinstance(combined_input, dict):
        combined_input = json.dumps(combined_input)
    
    logger.debug("Calling OpenAI API for preprocessing")
    
    # Use the combined input as the user_input for the preprocessing
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        response_format={ 
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": preprocessing_system_prompt
            },
            {
                "role": "user",
                "content": combined_input
            }
        ],
    )

    response_json = response.choices[0].message.content
    
    # Parse the response to ensure it's valid JSON
    try:
        parsed_response = json.loads(response_json)
        # Validate against our schema
        parsed_model = PreprocessingOutput.model_validate(parsed_response)
        log_parsed_json("preprocessing", parsed_response, parsed_model)
        logger.info("Step 1: Preprocessing completed successfully")
    except Exception as e:
        logger.error(f"Error parsing preprocessing response: {str(e)}")
        logger.error(f"Raw response: {response_json[:200]}...")
    
    return response_json

def project_details(preprocessed_data):
    """
    Generate detailed project information from preprocessed data.
    
    Args:
        preprocessed_data (str or dict): Preprocessed data from the preprocessing function
        
    Returns:
        str: JSON string with project details
    """
    logger.info("Step 2: Starting project details generation")
    
    # Parse the preprocessed data as JSON
    if isinstance(preprocessed_data, str):
        preprocessed_data = json.loads(preprocessed_data)
    
    # Extract project information from preprocessed data
    project_info = preprocessed_data.get("project", {})
    team_info = preprocessed_data.get("team", {})
    
    # Format team information for system prompt
    organization_info = team_info.get("organization", {})
    team_context = {
        "organization": {
            "name": organization_info.get("name", ""),
            "industry": organization_info.get("industry", ""),
            "members": organization_info.get("members", 0)
        },
        "team_context": team_info.get("team_context", ""),
        "team_members": team_info.get("team_members", [])
    }
    
    # Create a formatted team context string for the system prompt
    org_name = team_context["organization"]["name"] 
    org_industry = team_context["organization"]["industry"]
    org_members = team_context["organization"]["members"]
    team_context_str = team_context["team_context"]
    
    # Format the system prompt with the team information
    formatted_system_prompt = system_prompt.format(
        team_organization_name=org_name,
        team_organization_industry=org_industry,
        team_organization_members=org_members,
        team_team_context=team_context_str,
        team_members=team_context["team_members"]
    )
    
    # Safely format the project details prompt using our utility function
    replacement_dict = {
        "{project_info}": project_info.get("user_request", ""),
        "{project_description}": project_info.get("description", ""),
        "{project_team_context}": project_info.get("team_context", "")
    }
    safe_project_details_prompt = safe_format(project_details_prompt, replacement_dict)
    
    logger.debug("Calling OpenAI API for project details")
    
    # Call the API to generate project details
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": formatted_system_prompt
            },
            {
                "role": "user",
                "content": safe_project_details_prompt
            }
        ],
    )
    
    response_json = response.choices[0].message.content
    
    # Parse the response to ensure it's valid JSON
    try:
        parsed_response = json.loads(response_json)
        # Validate against our schema
        parsed_model = ProjectDetails.model_validate(parsed_response)
        log_parsed_json("project_details", parsed_response, parsed_model)
        logger.info("Step 2: Project details generation completed successfully")
    except Exception as e:
        logger.error(f"Error parsing project details response: {str(e)}")
        logger.error(f"Raw response: {response_json[:200]}...")
    
    return response_json

def tasks_generation(preprocessed_data, project_details_output):
    """
    Generate tasks for the project based on preprocessed data and project details.
    
    Args:
        preprocessed_data (str or dict): Preprocessed data from the preprocessing function
        project_details_output (str or dict): Project details from the project_details function
        
    Returns:
        str: JSON string with tasks
    """
    logger.info("Step 3: Starting tasks generation")
    
    # Parse the data as JSON if they are strings
    if isinstance(preprocessed_data, str):
        preprocessed_data = json.loads(preprocessed_data)
    if isinstance(project_details_output, str):
        project_details_output = json.loads(project_details_output)
    
    # Extract necessary information
    team_info = preprocessed_data.get("team", {})
    project_info = preprocessed_data.get("project", {})
    
    # Format team information for system prompt
    organization_info = team_info.get("organization", {})
    team_context = {
        "organization": {
            "name": organization_info.get("name", ""),
            "industry": organization_info.get("industry", ""),
            "members": organization_info.get("members", 0)
        },
        "team_context": team_info.get("team_context", ""),
        "team_members": team_info.get("team_members", [])
    }
    
    # Create a formatted team context string for the system prompt
    org_name = team_context["organization"]["name"] 
    org_industry = team_context["organization"]["industry"]
    org_members = team_context["organization"]["members"]
    team_context_str = team_context["team_context"]
    
    # Format the system prompt with the team information
    formatted_system_prompt = system_prompt.format(
        team_organization_name=org_name,
        team_organization_industry=org_industry,
        team_organization_members=org_members,
        team_team_context=team_context_str,
        team_members=team_context["team_members"]
    )
    
    # Extract detailed project information for rich context
    detailed_analysis = project_details_output.get("detailed_analyzis", {})
    roadmap = detailed_analysis.get("roadmap", [])
    objectives = project_details_output.get("objectives", [])
    key_points = project_details_output.get("key_points", [])
    
    # Create formatted roadmap, objectives, and key points for prompt
    roadmap_text = ""
    for i, step in enumerate(roadmap):
        roadmap_text += f"{i+1}. {step.get('title', '')}: {step.get('description', '')}\n"
    
    objectives_text = ""
    for i, obj in enumerate(objectives):
        objectives_text += f"{i+1}. {obj.get('objective', '')}: {obj.get('description', '')}\n"
    
    key_points_text = ""
    for i, point in enumerate(key_points):
        key_points_text += f"{i+1}. {point.get('key_point', '')}: {point.get('description', '')}\n"
    
    # Format team members for the prompt
    team_members_text = []
    for member in team_info.get("team_members", []):
        team_members_text.append(f"{member.get('name', '')}: {member.get('role', '')}")
    team_members_str = "\n".join(team_members_text)
    
    # Safely format the tasks prompt using our utility function
    replacement_dict = {
        "{project_title}": project_details_output.get("title", ""),
        "{project_description}": project_details_output.get("description", ""),
        "{original_request}": project_info.get("user_request", ""),
        "{detailed_description}": project_info.get("description", ""),
        "{project_summary}": detailed_analysis.get("summary", ""),
        "{draft_plan}": project_details_output.get("draft_plan", ""),
        "{roadmap}": roadmap_text,
        "{objectives}": objectives_text,
        "{key_points}": key_points_text,
        "{team_members}": team_members_str
    }
    safe_tasks_prompt = safe_format(tasks_prompt, replacement_dict)
    
    logger.debug("Calling OpenAI API for tasks generation")
    
    # Call the API to generate tasks
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": formatted_system_prompt
            },
            {
                "role": "user",
                "content": safe_tasks_prompt
            }
        ],
    )
    
    response_json = response.choices[0].message.content
    
    # Parse the response to ensure it's valid JSON
    try:
        parsed_response = json.loads(response_json)
        
        # Check if the response is wrapped in a 'tasks' object and handle it
        # This handles the case where the API returns {"tasks": [...]} instead of just [...]
        if isinstance(parsed_response, dict) and "tasks" in parsed_response:
            logger.info("Detected tasks wrapped in 'tasks' object, extracting tasks array")
            tasks_array = parsed_response["tasks"]
            if isinstance(tasks_array, list):
                # Update the response_json to be just the tasks array
                response_json = json.dumps(tasks_array)
                parsed_response = tasks_array
            else:
                raise ValueError(f"'tasks' field is not an array: {type(tasks_array)}")
        
        # Validate tasks array against our schema
        task_list_adapter = TypeAdapter(List[Task])
        parsed_model = task_list_adapter.validate_python(parsed_response)
        log_parsed_json("tasks_generation", parsed_response)
        logger.info(f"Step 3: Tasks generation completed successfully with {len(parsed_model)} tasks")
    except Exception as e:
        logger.error(f"Error parsing tasks generation response: {str(e)}")
        logger.error(f"Raw response: {response_json[:200]}...")
        # Return an empty array as a fallback to prevent downstream errors
        return "[]"
    
    return response_json

def generate_calendar(preprocessed_data, project_details_output, tasks_output):
    """
    Generate a calendar based on preprocessed data, project details, and tasks.
    
    Args:
        preprocessed_data (str or dict): Preprocessed data from the preprocessing function
        project_details_output (str or dict): Project details from the project_details function
        tasks_output (str or dict): Tasks from the tasks_generation function
        
    Returns:
        str: JSON string with calendar
    """
    logger.info("Step 4: Starting calendar generation")
    
    # Parse the data as JSON if they are strings
    if isinstance(preprocessed_data, str):
        preprocessed_data = json.loads(preprocessed_data)
    if isinstance(project_details_output, str):
        project_details_output = json.loads(project_details_output)
    
    # Safely parse tasks_output
    parsed_tasks = []
    try:
        if isinstance(tasks_output, str):
            parsed_tasks = json.loads(tasks_output)
        elif isinstance(tasks_output, list):
            parsed_tasks = tasks_output
        else:
            logger.warning(f"Unexpected tasks_output type: {type(tasks_output)}, using empty array")
    except Exception as e:
        logger.error(f"Error parsing tasks_output: {str(e)}")
        logger.error(f"Raw tasks_output: {str(tasks_output)[:200]}")
        # Continue with an empty array to prevent cascading failures
    
    logger.info(f"Processing {len(parsed_tasks)} tasks for calendar generation")
    
    # Extract necessary information
    team_info = preprocessed_data.get("team", {})
    project_info = preprocessed_data.get("project", {})
    
    # Format team information for system prompt
    organization_info = team_info.get("organization", {})
    team_context = {
        "organization": {
            "name": organization_info.get("name", ""),
            "industry": organization_info.get("industry", ""),
            "members": organization_info.get("members", 0)
        },
        "team_context": team_info.get("team_context", ""),
        "team_members": team_info.get("team_members", [])
    }
    
    # Create a formatted team context string for the system prompt
    org_name = team_context["organization"]["name"] 
    org_industry = team_context["organization"]["industry"]
    org_members = team_context["organization"]["members"]
    team_context_str = team_context["team_context"]
    
    # Format the system prompt with the team information
    formatted_system_prompt = system_prompt.format(
        team_organization_name=org_name,
        team_organization_industry=org_industry,
        team_organization_members=org_members,
        team_team_context=team_context_str,
        team_members=team_context["team_members"]
    )
    
    # Get current date for project start
    today = datetime.datetime.now()
    current_date = today.strftime("%Y-%m-%d")
    logger.debug(f"Using start date: {current_date}")
    
    # Pre-process tasks to add IDs and categorize them
    enhanced_tasks = []
    task_categories = {
        "meeting": ["meeting", "workshop", "review", "coordination", "session", "interview", "recruitment", "presentation"],
        "research": ["research", "analysis", "study", "investigation", "exploration"],
        "design": ["design", "wireframing", "prototype", "blueprint", "architecture", "schema"],
        "development": ["development", "implementation", "integration", "creation", "building"],
        "testing": ["testing", "benchmarking", "audit", "assessment", "evaluation"],
        "documentation": ["documentation", "guide", "manual"],
        "marketing": ["marketing", "sales", "demo", "collateral"]
    }
    
    category_counts = {category: 0 for category in task_categories.keys()}
    category_counts["other"] = 0
    
    for i, task in enumerate(parsed_tasks):
        # Make sure task is a dict and not a string
        if not isinstance(task, dict):
            logger.warning(f"Task at index {i} is not a dictionary: {type(task)}")
            continue
            
        task_name = task.get("task_name", "").lower()
        task_tag = "other"
        
        # Categorize tasks based on keywords in their names or descriptions
        for category, keywords in task_categories.items():
            if any(keyword in task_name.lower() for keyword in keywords) or any(keyword in task.get("description", "").lower() for keyword in keywords):
                task_tag = category
                break
        
        # Increment the category count
        category_counts[task_tag] += 1
        
        enhanced_tasks.append({
            "task_id": f"TASK-{i+1:03d}",
            "task_name": task.get("task_name", ""),
            "description": task.get("description", ""),
            "assignee": task.get("assignee", ""),
            "dependencies": task.get("dependencies", []),
            "estimated_hours": task.get("estimated_hours", 0),
            "status": task.get("status", "Not Started"),
            "priority": task.get("priority", "Medium"),
            "tag": task_tag
        })
    
    # Log task categorization results
    logger.info("Task categories distribution:")
    for category, count in category_counts.items():
        if count > 0:
            logger.info(f"  - {category}: {count} tasks")
    
    # If no tasks were processed, create a minimal placeholder task for the calendar
    if not enhanced_tasks:
        logger.warning("No valid tasks found. Creating a placeholder task.")
        enhanced_tasks.append({
            "task_id": "TASK-001",
            "task_name": "Project Planning",
            "description": "Initial project planning and setup",
            "assignee": "Project Manager",
            "dependencies": [],
            "estimated_hours": 8,
            "status": "Not Started",
            "priority": "High",
            "tag": "planning"
        })
    
    # Safely format the calendar prompt using our utility function
    replacement_dict = {
        "{current_date}": current_date,
        "{project_title}": project_details_output.get("title", ""),
        "{project_description}": project_details_output.get("description", ""),
        "{draft_plan}": project_details_output.get("draft_plan", ""),
        "{enhanced_tasks}": json.dumps(enhanced_tasks, indent=2)
    }
    safe_calendar_prompt = safe_format(calendar_prompt, replacement_dict)
    
    logger.debug("Calling OpenAI API for calendar generation")
    
    # Call the API to generate calendar
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": formatted_system_prompt
            },
            {
                "role": "user",
                "content": safe_calendar_prompt
            }
        ],
    )
    
    response_json = response.choices[0].message.content
    
    # Parse the response to ensure it's valid JSON
    try:
        parsed_response = json.loads(response_json)
        
        # Check if the response is wrapped in a 'schedule' object
        if isinstance(parsed_response, dict) and "schedule" in parsed_response:
            logger.info("Detected schedule wrapper in calendar response, extracting schedule array")
            calendar_tasks = parsed_response["schedule"]
        else:
            calendar_tasks = parsed_response
            
        # Try to validate if it's a list
        if not isinstance(calendar_tasks, list):
            logger.error(f"Calendar tasks is not a list: {type(calendar_tasks)}")
            calendar_tasks = []
        
        # Validate if each task has required fields
        valid_tasks = []
        for task in calendar_tasks:
            if isinstance(task, dict) and "task_id" in task and "start_date" in task and "end_date" in task:
                valid_tasks.append(task)
            else:
                logger.warning(f"Skipping invalid calendar task: {task}")
        
        if valid_tasks:
            logger.info(f"Step 4: Calendar generation completed successfully with {len(valid_tasks)} calendar entries")
            # Convert back to JSON string for return
            response_json = json.dumps(valid_tasks)
        else:
            logger.warning("No valid calendar tasks found after validation")
            response_json = "[]"
    except Exception as e:
        logger.error(f"Error parsing calendar generation response: {str(e)}")
        logger.error(f"Raw response: {response_json[:200]}...")
        # Return an empty JSON array to avoid further errors
        response_json = "[]"
    
    return response_json, enhanced_tasks

def collect_and_process_outputs(preprocessed_data, project_details_output, tasks_output, calendar_output, enhanced_tasks):
    """
    Collect and process all outputs to create a unified project representation.
    
    Args:
        preprocessed_data (str or dict): Preprocessed data from the preprocessing function
        project_details_output (str or dict): Project details from the project_details function
        tasks_output (str or dict): Tasks from the tasks_generation function
        calendar_output (str or dict): Calendar from the generate_calendar function
        enhanced_tasks (list): Enhanced tasks list with tags and IDs
        
    Returns:
        dict: Unified project representation
    """
    logger.info("Step 5: Starting output aggregation and analytics")
    
    # Parse all outputs as JSON if they are strings
    try:
        if isinstance(preprocessed_data, str):
            preprocessed_data = json.loads(preprocessed_data)
        if isinstance(project_details_output, str):
            project_details_output = json.loads(project_details_output)
        if isinstance(tasks_output, str):
            tasks_output = json.loads(tasks_output)
        if isinstance(calendar_output, str):
            calendar_output = json.loads(calendar_output)
            
        # Handle calendar output that might be wrapped in a 'schedule' object
        if isinstance(calendar_output, dict) and 'schedule' in calendar_output:
            logger.info("Detected calendar output wrapped in 'schedule' object, extracting tasks array")
            calendar_output = calendar_output.get('schedule', [])
    except Exception as e:
        logger.error(f"Error parsing input data: {str(e)}")
        # Initialize empty objects as fallbacks
        if not isinstance(preprocessed_data, dict):
            preprocessed_data = {}
        if not isinstance(project_details_output, dict):
            project_details_output = {}
        if not isinstance(tasks_output, list):
            tasks_output = []
        if not isinstance(calendar_output, list):
            calendar_output = []
    
    # Initialize default values
    project_start = None
    project_end = None
    total_hours = 0
    tag_stats = {}
    team_workload = {}
    
    # Calculate project timeline only if we have valid calendar entries
    if calendar_output and all(isinstance(task, dict) for task in calendar_output):
        try:
            # Filter out any tasks that might be missing required date fields
            valid_calendar_tasks = [task for task in calendar_output 
                                  if isinstance(task, dict) and "start_date" in task and "end_date" in task]
            
            if valid_calendar_tasks:
                start_dates = [datetime.datetime.strptime(task["start_date"], "%Y-%m-%d") for task in valid_calendar_tasks]
                end_dates = [datetime.datetime.strptime(task["end_date"], "%Y-%m-%d") for task in valid_calendar_tasks]
                
                project_start = min(start_dates).strftime("%Y-%m-%d") if start_dates else None
                project_end = max(end_dates).strftime("%Y-%m-%d") if end_dates else None
                
                if project_start and project_end:
                    logger.info(f"Project timeline: {project_start} to {project_end}")
            else:
                logger.warning("No valid calendar tasks with dates found")
        except Exception as e:
            logger.error(f"Error calculating project timeline: {str(e)}")
            # Keep the default values
    else:
        logger.warning("No valid calendar entries found for timeline calculation")
    
    # Calculate total estimated hours only if we have valid task entries
    if tasks_output and all(isinstance(task, dict) for task in tasks_output):
        try:
            total_hours = sum(task.get("estimated_hours", 0) for task in tasks_output)
            logger.info(f"Total estimated hours: {total_hours}")
        except Exception as e:
            logger.error(f"Error calculating total hours: {str(e)}")
            # Keep the default value
    else:
        logger.warning("No valid task entries found for hours calculation")
    
    # Create tag statistics only if we have valid calendar entries
    if calendar_output and all(isinstance(task, dict) for task in calendar_output):
        try:
            for task in calendar_output:
                if not isinstance(task, dict):
                    continue
                    
                tag = task.get("tag", "other")
                if tag not in tag_stats:
                    tag_stats[tag] = {
                        "count": 0,
                        "total_days": 0
                    }
                
                tag_stats[tag]["count"] += 1
                
                # Calculate days for this task if dates are available
                if "start_date" in task and "end_date" in task:
                    try:
                        start = datetime.datetime.strptime(task["start_date"], "%Y-%m-%d")
                        end = datetime.datetime.strptime(task["end_date"], "%Y-%m-%d")
                        days = (end - start).days + 1
                        tag_stats[tag]["total_days"] += days
                    except Exception as e:
                        logger.error(f"Error calculating days for task: {str(e)}")
        except Exception as e:
            logger.error(f"Error calculating tag statistics: {str(e)}")
            # Keep the default value
    else:
        logger.warning("No valid calendar entries found for tag statistics")
    
    # Calculate workload per team member only if we have valid calendar and task entries
    if calendar_output and tasks_output and all(isinstance(task, dict) for task in calendar_output):
        try:
            for task in calendar_output:
                if not isinstance(task, dict):
                    continue
                    
                assignee = task.get("assignee", "Unassigned")
                if assignee not in team_workload:
                    team_workload[assignee] = {
                        "task_count": 0,
                        "estimated_hours": 0
                    }
                
                team_workload[assignee]["task_count"] += 1
                
                # Find matching task in tasks_output to get hours
                task_name = task.get("task_name", "")
                if task_name:
                    for original_task in tasks_output:
                        if not isinstance(original_task, dict):
                            continue
                            
                        if original_task.get("task_name") == task_name:
                            team_workload[assignee]["estimated_hours"] += original_task.get("estimated_hours", 0)
                            break
            
            # Log team workload statistics
            logger.info("Team workload distribution:")
            for member, stats in team_workload.items():
                logger.info(f"  - {member}: {stats['task_count']} tasks, {stats['estimated_hours']} hours")
        except Exception as e:
            logger.error(f"Error calculating team workload: {str(e)}")
            # Keep the default value
    else:
        logger.warning("No valid calendar or task entries found for workload calculation")
    
    # Create a summary of the project
    try:
        team_name = ""
        if isinstance(preprocessed_data, dict) and "team" in preprocessed_data:
            team_data = preprocessed_data.get("team", {})
            if isinstance(team_data, dict) and "organization" in team_data:
                org_data = team_data.get("organization", {})
                if isinstance(org_data, dict):
                    team_name = org_data.get("name", "")
        logger.debug(f"Extracted team name: {team_name}")
    except Exception as e:
        logger.error(f"Error extracting team name: {str(e)}")
        team_name = ""
    
    # Calculate total days only if we have valid start and end dates
    total_days = None
    if project_start and project_end:
        try:
            total_days = (datetime.datetime.strptime(project_end, "%Y-%m-%d") - 
                          datetime.datetime.strptime(project_start, "%Y-%m-%d")).days + 1
        except Exception as e:
            logger.error(f"Error calculating total days: {str(e)}")
        
    project_summary = {
        "project": {
            "title": project_details_output.get("title", ""),
            "description": project_details_output.get("description", ""),
            "start_date": project_start,
            "end_date": project_end,
            "total_estimated_hours": total_hours,
            "total_days": total_days,
            "team": team_name,
            "objectives": project_details_output.get("objectives", []),
            "key_points": project_details_output.get("key_points", [])
        },
        "roadmap": project_details_output.get("detailed_analyzis", {}).get("roadmap", []),
        "tasks": tasks_output,
        "enhanced_tasks": enhanced_tasks,
        "calendar": calendar_output,
        "statistics": {
            "task_categories": tag_stats,
            "team_workload": team_workload
        }
    }
    
    logger.info("Step 5: Output aggregation and analytics completed")
    
    # Log summary information, handling potential missing data
    title = project_details_output.get("title", "Untitled Project")
    task_count = len(tasks_output) if isinstance(tasks_output, list) else 0
    days_str = f"across {total_days} days" if total_days else ""
    logger.info(f"Project summary created: '{title}' with {task_count} tasks {days_str}")
    
    # Log summary statistics with error handling
    try:
        stats_dict = {
            'title': project_details_output.get('title', ''),
            'total_tasks': task_count,
            'total_days': total_days,
            'total_hours': total_hours,
            'team_members': len(team_workload),
            'task_categories': len(tag_stats)
        }
        logger.debug(f"Project summary statistics: {json.dumps(stats_dict)}")
    except Exception as e:
        logger.error(f"Error logging summary statistics: {str(e)}")
    
    return project_summary

def run_generative_project_management(user_input, team_context):
    """
    Run the complete generative project management pipeline.
    
    Args:
        user_input (str): User's project request
        team_context (dict): Information about the team and organization
        
    Returns:
        dict: Complete project management plan
    """
    logger.info("Starting generative project management pipeline")
    
    start_time = datetime.datetime.now()
    
    # Step 1: Preprocessing
    preprocessed_data = preprocessing(user_input, team_context)
    
    # Step 2: Project Details
    project_details_output = project_details(preprocessed_data)
    
    # Step 3: Tasks Generation
    tasks_output = tasks_generation(preprocessed_data, project_details_output)
    
    # Step 4: Calendar Generation
    calendar_output, enhanced_tasks = generate_calendar(preprocessed_data, project_details_output, tasks_output)
    
    # Step 5: Collect and Process Outputs
    project_summary = collect_and_process_outputs(preprocessed_data, project_details_output, tasks_output, calendar_output, enhanced_tasks)
    
    end_time = datetime.datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    logger.info(f"Generative project management pipeline completed in {execution_time:.2f} seconds")
    
    return project_summary

# Example usage
if __name__ == "__main__":
    logger.info("=== Generative Project Management Script Started ===")
    
    # Check if prompts directory exists and contains necessary files
    if not (PROMPTS_DIR.exists() and all((PROMPTS_DIR / f).exists() for f in ["system_prompt.txt", "preprocessing_prompt.txt", "project_details_prompt.txt", "tasks_prompt.txt", "calendar_prompt.txt"])):
        logger.error(f"Prompts directory not found or missing required prompt files in {PROMPTS_DIR}")
        raise FileNotFoundError(f"Prompts directory not found or missing required prompt files in {PROMPTS_DIR}")
    
    try:
        # Load example data
        logger.info("Loading company data from input_data/company_data.json")
        with open('input_data/company_data.json', 'r') as f:
            team_context = json.load(f)
        
        # Load user input from text file
        logger.info("Loading user input from input_data/user_input.txt")
        with open('input_data/user_input.txt', 'r') as f:
            user_input = f.read().strip()
        
        # Run the pipeline
        project_plan = run_generative_project_management(user_input, team_context)
        
        # Save the output
        logger.info("Saving project plan to project_plan.json")
        with open('project_plan.json', 'w') as f:
            json.dump(project_plan, f, indent=2)
        
        logger.info("Project plan generated and saved to 'project_plan.json'")
        logger.info("=== Generative Project Management Script Completed ===")
    
    except Exception as e:
        logger.exception(f"Error during execution: {str(e)}")
        raise 