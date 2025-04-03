import json
from modules.utils import client, logger, load_prompt, log_parsed_json
from modules.models import PreprocessingOutput

# Load the system prompt for preprocessing
preprocessing_system_prompt = load_prompt("preprocessing_prompt.txt")

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