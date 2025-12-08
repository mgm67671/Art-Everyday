from datetime import date
import os

def get_daily_prompt():
    """
    Get the daily prompt based on the day of the year.
    Cycles through prompts in website/prompts.txt
    """
    try:
        prompts_file = os.path.join(os.path.dirname(__file__), 'prompts.txt')
        with open(prompts_file, 'r') as f:
            prompts = [line.strip() for line in f.readlines() if line.strip()]
        
        if not prompts:
            return "Artistic Expression"
        
        # Use day of year (0-365) to cycle through prompts
        day_of_year = date.today().timetuple().tm_yday - 1
        prompt_index = day_of_year % len(prompts)
        return prompts[prompt_index]
    except Exception as e:
        print(f"Error reading prompts: {e}")
        return "Artistic Expression"
