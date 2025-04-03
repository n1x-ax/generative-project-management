import json
import datetime
from modules.utils import logger

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