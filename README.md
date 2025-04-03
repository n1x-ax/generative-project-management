# Generative Project Management

This repository is the official implementation of the concepts discussed in the article [Generative Project Management](https://alexnix.com/blog/posts/en/generative-project-management).

## What is Generative Project Management?

Generative Project Management is a paradigm shift in how we approach project planning and execution. By leveraging large language models (LLMs) and structured prompting, we can transform vague project ideas into comprehensive, actionable plans in minutes rather than days or weeks.

The system takes a basic project description and team context as input, and generates:

1. A detailed project plan with title, description, and objectives
2. A structured roadmap with execution steps
3. Task breakdown with assigned team members, dependencies, and time estimates
4. A realistic project calendar/schedule
5. Project analytics including workload distribution and timeline projections

## Article and Repository Connection

- **The Article** provides the theoretical foundation, explains the architecture, and demonstrates the potential of AI-driven project management.
- **This Repository** provides the practical implementation with working code that you can use, customize, and extend for your own projects.

## Project Architecture

The system follows a pipeline architecture with three main blocks:

1. **Project Details**: Processes user input and team context to generate project information
2. **Task Generation**: Creates detailed tasks with assignments and dependencies
3. **Generative Calendar**: Schedules tasks with realistic dates and times

<div align="center">
  <img src="https://alexnix.com/images/research/oneshot/schema.jpg" alt="Generative Management Schema" width="80%">
</div>

## Files and Structure

- `generative_project_management.py` - The main Python script with all the implementation
- `run_modular.py` - Entry point for the modular implementation
- `modules/` - Directory containing modular components (see modules/README.md for details)
- `input_data/` - Directory containing input files:
  - `company_data.json` - Example company/team data in JSON format
  - `user_input.txt` - Example project description as plain text
- `requirements.txt` - Required Python dependencies
- `prompts/` - Directory containing all text prompts used by the system

## Prerequisites

- Python 3.7+
- OpenAI API key

## Installation

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-api-key'
   ```
   
   Alternatively, create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY='your-api-key'
   ```

## Usage

1. Prepare your company data in JSON format following the structure in `input_data/company_data.json`:
   ```json
   {
     "organization": {
       "name": "Your Company",
       "about": "Description of your company"
     },
     "team_members": [
       {
         "name": "Team Member 1",
         "role": "Role 1",
         "responsibilities": "Responsibilities"
       },
       ...
     ]
   }
   ```

2. Create a text file with your project description in `input_data/user_input.txt`:
   ```
   A detailed description of the project you want to plan
   ```

3. Run the script:
   ```
   python generative_project_management.py
   ```

4. The script will generate a comprehensive project plan and save it as `project_plan.json`

## Output

The generated output includes:

- Project summary (title, description, objectives)
- Roadmap with execution phases
- Detailed task list with assignments and dependencies
- Calendar with start/end dates for each task
- Analytics on task categories and team workload

## Modular Implementation

This repository includes both a single-file implementation (`generative_project_management.py`) and a modular implementation in the `modules/` directory. The modular version breaks the functionality into separate components that can be used independently:

- `modules/preprocessing.py`: Step 1 - Preprocessing user input and team context
- `modules/project_details.py`: Step 2 - Generating detailed project information
- `modules/tasks_generation.py`: Step 3 - Generating tasks based on project details
- `modules/calendar_generation.py`: Step 4 - Creating a calendar/schedule for tasks
- `modules/output_processor.py`: Step 5 - Processing and aggregating output data

To use the modular version, run:
```
python run_modular.py
```

## Example Integration

```python
# Import module
from generative_project_management import run_generative_project_management

# Load team context
with open('input_data/my_company.json', 'r') as f:
    team_context = json.load(f)

# Define project
project_description = "Build a mobile app that helps users track their fitness goals"

# Generate project plan
project_plan = run_generative_project_management(project_description, team_context)

# Use the plan
print(f"Project title: {project_plan['project']['title']}")
```

## Customization

You can customize the system by:

- Modifying the prompt text files in the `prompts/` directory
- Adjusting the API parameters in the Python code
- Adding additional processing steps

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Learn More

For a deep dive into the concepts, architecture, and potential of Generative Project Management, read the full article at [alexnix.com/blog/posts/en/generative-project-management](https://alexnix.com/blog/posts/en/generative-project-management). 