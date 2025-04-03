# Modular Generative Project Management

This directory contains a modular implementation of the Generative Project Management system.

## Module Structure

- `__init__.py`: Makes the directory a proper Python package
- `utils.py`: Common utility functions and configuration
- `models.py`: Pydantic models and data schemas
- `preprocessing.py`: Step 1 - Preprocessing user input and team context
- `project_details.py`: Step 2 - Generating detailed project information
- `tasks_generation.py`: Step 3 - Generating tasks based on project details
- `calendar_generation.py`: Step 4 - Creating a calendar/schedule for tasks
- `output_processor.py`: Step 5 - Processing and aggregating output data
- `main.py`: Orchestration of the entire pipeline

## Usage

The modules can be used together through the `run_modular.py` script in the parent directory, or individually for specific purposes.

### Individual Module Usage

```python
# Example of using individual modules
from modules.preprocessing import preprocessing
from modules.project_details import project_details

# Load user input and team context
user_input = "Create a marketing campaign for our new product"
team_context = {...}  # Team and organization information

# Run preprocessing step
preprocessed_data = preprocessing(user_input, team_context)

# Generate project details
project_details_output = project_details(preprocessed_data)

# Use the output as needed
print(project_details_output)
```

### Complete Pipeline

```python
# Using the complete pipeline
from modules.main import run_generative_project_management

user_input = "Create a marketing campaign for our new product"
team_context = {...}  # Team and organization information

# Run the entire pipeline
project_plan = run_generative_project_management(user_input, team_context)

# Use the complete project plan
print(project_plan["project"]["title"])
```

## Design Principles

1. **Modularity**: Each step is separated into its own module for clarity and reusability
2. **Error Resilience**: Robust error handling throughout to prevent cascading failures
3. **Consistent Interfaces**: Clear input/output contracts between modules
4. **Logging**: Comprehensive logging for debugging and monitoring
5. **Data Validation**: Schema validation using Pydantic models 