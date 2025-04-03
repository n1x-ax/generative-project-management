import json
import datetime
from modules.utils import logger
from modules.preprocessing import preprocessing
from modules.project_details import project_details
from modules.tasks_generation import tasks_generation
from modules.calendar_generation import generate_calendar
from modules.output_processor import collect_and_process_outputs

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

# Add a __main__ block to support running this module directly
if __name__ == "__main__":
    import os
    import pathlib
    
    logger.info("=== Generative Project Management Script Started ===")
    
    # Get prompts directory relative to this file
    PROMPTS_DIR = pathlib.Path(__file__).parent.parent / "prompts"
    
    # Check if prompts directory exists and contains necessary files
    if not (PROMPTS_DIR.exists() and all((PROMPTS_DIR / f).exists() for f in [
            "system_prompt.txt", 
            "preprocessing_prompt.txt", 
            "project_details_prompt.txt", 
            "tasks_prompt.txt", 
            "calendar_prompt.txt"])):
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