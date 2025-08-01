import csv
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

def load_tasks_from_csv(filename="tasks_export_example.csv"):
    tasks = []
    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            task = {
                "name": row["Task"],
                "completed": row["Completed"].lower() == "true",
                "created_at": datetime.strptime(row["Created At"], "%Y-%m-%d"),
                "completed_at": datetime.strptime(row["Completed At"], "%Y-%m-%d") if row["Completed At"] else None,
            }
            tasks.append(task)
        return tasks

def analyze_productivity(tasks):
    created_per_day = defaultdict(int)
    completed_per_day = defaultdict(int)

    # Find min and max dates to establish the complete range
    if not tasks:
        # Return empty dictionaries if no tasks are present
        return defaultdict(int), defaultdict(int)

    all_task_dates = [t["created_at"].date() for t in tasks]
    all_task_dates.extend([t["completed_at"].date() for t in tasks if t["completed_at"]])
    
    # Handle case where no valid dates exist (though created_at should always be present)
    if not all_task_dates:
        return defaultdict(int), defaultdict(int)

    min_date = min(all_task_dates)
    max_date = max(all_task_dates)

    # Ensure all days in the range are included in the dictionaries
    current_date = min_date
    while current_date <= max_date:
        created_per_day[current_date] = 0
        completed_per_day[current_date] = 0
        current_date += timedelta(days=1)

    # Populate actual task counts
    for task in tasks:
        created_day = task["created_at"].date()
        created_per_day[created_day] += 1

        if task["completed"] and task["completed_at"]:
            completed_day = task["completed_at"].date()
            completed_per_day[completed_day] += 1

    return created_per_day, completed_per_day

def plot_productivity(created_per_day, completed_per_day):
    # Get all unique dates sorted chronologically
    all_days = sorted(set(created_per_day.keys()) | set(completed_per_day.keys()))

    # Extract daily counts for plotting
    created_counts_for_plot = [created_per_day.get(day, 0) for day in all_days]
    completed_counts_for_plot = [completed_per_day.get(day, 0) for day in all_days]

    # Calculate pending tasks per day (cumulative)
    pending_tasks_over_time = []
    current_active_tasks = 0  # Running count of active (pending) tasks

    for day in all_days:
        # Add newly created tasks and subtract completed tasks
        current_active_tasks += created_per_day.get(day, 0)
        current_active_tasks -= completed_per_day.get(day, 0)
        
        # Prevent negative task count (can happen with inconsistent data)
        pending_tasks_over_time.append(max(0, current_active_tasks))

    plt.figure(figsize=(12, 7))

    plt.plot(all_days, created_counts_for_plot, label="Tasks Created (Daily)", marker="o", linestyle='-', color='blue')
    plt.plot(all_days, completed_counts_for_plot, label="Tasks Completed (Daily)", marker="o", linestyle='-', color='green')
    plt.plot(all_days, pending_tasks_over_time, label="Pending Tasks (Cumulative)", marker="x", linestyle='--', color='red', linewidth=2)

    plt.xlabel("Date")
    plt.ylabel("Number of Tasks")
    plt.title("Productivity and Pending Task Trends")
    plt.legend()
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')

    # Ensure Y-axis only shows integers
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.show()

if __name__ == "__main__":
    tasks = load_tasks_from_csv()
    created_data, completed_data = analyze_productivity(tasks)
    plot_productivity(created_data, completed_data)
