import json
from pydantic import TypeAdapter
from typing import List
from modules.utils import client, logger, load_prompt, log_parsed_json, safe_format
from modules.models import Task

# Load prompts from files
system_prompt = load_prompt("system_prompt.txt")
tasks_prompt = load_prompt("tasks_prompt.txt")

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