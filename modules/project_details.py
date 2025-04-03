import json
from modules.utils import client, logger, load_prompt, log_parsed_json, safe_format
from modules.models import ProjectDetails

# Load prompts from files
system_prompt = load_prompt("system_prompt.txt")
project_details_prompt = load_prompt("project_details_prompt.txt")

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