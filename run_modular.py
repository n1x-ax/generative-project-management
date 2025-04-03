#!/usr/bin/env python3
"""
Modular Generative Project Management Script
This script uses the modularized components to run the project management pipeline.
"""

import json
import sys
from modules.main import run_generative_project_management
from modules.utils import logger

if __name__ == "__main__":
    logger.info("=== Modular Generative Project Management Started ===")
    
    try:
        # Load company data
        logger.info("Loading company data from input_data/company_data.json")
        with open('input_data/company_data.json', 'r') as f:
            team_context = json.load(f)
        
        # Load user input from text file or command line
        if len(sys.argv) > 1:
            # User input provided as command line argument
            user_input = sys.argv[1]
            logger.info("User input provided via command line")
        else:
            # Load from file
            logger.info("Loading user input from input_data/user_input.txt")
            with open('input_data/user_input.txt', 'r') as f:
                user_input = f.read().strip()
        
        # Run the pipeline
        project_plan = run_generative_project_management(user_input, team_context)
        
        # Save the output
        output_file = 'modular_project_plan.json'
        logger.info(f"Saving project plan to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(project_plan, f, indent=2)
        
        logger.info(f"Project plan generated and saved to '{output_file}'")
        logger.info("=== Modular Generative Project Management Completed ===")
    
    except Exception as e:
        logger.exception(f"Error during execution: {str(e)}")
        sys.exit(1)
    
    sys.exit(0) 