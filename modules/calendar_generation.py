import json
import datetime
from modules.utils import client, logger, load_prompt, log_parsed_json, safe_format
from modules.models import CalendarTask

# Load prompts from files
system_prompt = load_prompt("system_prompt.txt")
calendar_prompt = load_prompt("calendar_prompt.txt")

def generate_calendar(preprocessed_data, project_details_output, tasks_output):
    """
    Generate a calendar based on preprocessed data, project details, and tasks.
    
    Args:
        preprocessed_data (str or dict): Preprocessed data from the preprocessing function
        project_details_output (str or dict): Project details from the project_details function
        tasks_output (str or dict): Tasks from the tasks_generation function
        
    Returns:
        tuple: (str: JSON string with calendar, list: enhanced tasks with tags and IDs)
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