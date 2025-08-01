# Import required libraries
import flet as ft 
import json 
import os 
import csv
from datetime import datetime
from collections import defaultdict

# Class to represent each individual task in the list
class Task(ft.Column): 
    def __init__(self, task_name, task_status_change, task_delete, created_at=None, completed_at=None): 
        super().__init__() 
        self.completed = False 
        self.task_name = task_name 
        self.task_status_change = task_status_change 
        self.task_delete = task_delete
        self.created_at = datetime.now().strftime("%Y-%m-%d")
        self.completed_at = None

        # Register creation date if not provided
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d")
        self.completed_at = completed_at
        
        # View to display the task
        self.display_task = ft.Checkbox( 
            value=False, label=self.task_name, on_change=self.status_changed) 
        self.edit_name = ft.TextField(expand=1) 

        self.display_view = ft.Row( 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[ 
                self.display_task, 
                ft.Row( 
                    spacing=0, 
                    controls=[ 
                        ft.IconButton( 
                            icon=ft.Icons.CREATE_OUTLINED, 
                            tooltip="Edit To-Do", 
                            on_click=self.edit_clicked, 
                        ), 
                        ft.IconButton( 
                            ft.Icons.DELETE_OUTLINE, 
                            tooltip="Delete To-Do", 
                            on_click=self.delete_clicked, 
                        ), 
                    ], 
                ), 
            ], 
        ) 

        # View for editing the task
        self.edit_view = ft.Row( 
            visible=False, 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[ 
                self.edit_name, 
                ft.IconButton( 
                    icon=ft.Icons.DONE_OUTLINE_OUTLINED, 
                    icon_color=ft.Colors.GREEN, 
                    tooltip="Update To-Do", 
                    on_click=self.save_clicked, 
                ), 
            ], 
        ) 

        self.controls = [self.display_view, self.edit_view] 

    def status_changed(self, e):
        self.completed = self.display_task.value
        if self.completed:
            self.completed_at = datetime.now().strftime("%Y-%m-%d")
        else:
            self.completed_at = None
        self.task_status_change(e)

    def edit_clicked(self, e): 
        """Switch to edit view."""
        self.edit_name.value = self.display_task.label 
        self.display_view.visible = False 
        self.edit_view.visible = True 
        self.update() 

    def save_clicked(self, e): 
        """Save the edited task and switch back to display view."""
        self.display_task.label = self.edit_name.value 
        self.display_view.visible = True 
        self.edit_view.visible = False 
        self.update() 

    def delete_clicked(self, e): 
        """Call the function to delete the task."""
        self.task_delete(self) 


# Main application class
class TodoApp(ft.Column): 
    def __init__(self, page): 
        super().__init__() 
        self.page = page 
        
        # Configure snackbar
        self.page.snack_bar = ft.SnackBar( 
            content=ft.Text(""), show_close_icon=True 
        ) 
        self.page.overlay.append(self.page.snack_bar) 
        
        # UI elements
        self.new_task = ft.TextField(hint_text="What needs to be done?", expand=True, on_submit=self.add_clicked) 
        self.tasks = ft.Column() 
        self.filter = ft.Tabs( 
            selected_index=0, 
            on_change=self.tabs_changed, 
            tabs=[ft.Tab(text="all"), ft.Tab(text="active"), ft.Tab(text="completed")], 
        ) 
        self.items_left = ft.Text("0 items left") 
        self.width = 600 

        # Application layout
        self.controls = [ 
            ft.Row( 
                [ft.Text(value="Todos", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)], 
                alignment=ft.MainAxisAlignment.CENTER, 
            ), 
            ft.Row( 
                controls=[ 
                    self.new_task, 
                    ft.FloatingActionButton( 
                        icon=ft.Icons.ADD, on_click=self.add_clicked 
                    ), 
                ], 
            ), 
            ft.Column( 
                spacing=25, 
                controls=[ 
                    self.filter, 
                    self.tasks, 
                    ft.Row( 
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
                        vertical_alignment=ft.CrossAxisAlignment.CENTER, 
                        controls=[ 
                            self.items_left, 
                            ft.Row( 
                                controls=[ 
                                    ft.OutlinedButton( 
                                        text="Export to CSV", on_click=self.export_tasks_csv 
                                    ), 
                                    ft.OutlinedButton( 
                                        text="Clear completed", on_click=self.clear_clicked 
                                    ), 
                                ], 
                            ), 
                        ], 
                    ), 
                ], 
            ), 
        ] 
        self.load_tasks() 

    def add_clicked(self, e): 
        """Add a new task if the input field is not empty."""
        if self.new_task.value.strip() == "": 
            return 
        task = Task(self.new_task.value, self.task_status_change, self.task_delete) 
        self.tasks.controls.append(task) 
        self.new_task.value = "" 
        self.update() 
        self.save_tasks() 
    
    def task_status_change(self, e): 
        """Update UI and save when a task status changes."""
        self.update() 
        self.save_tasks() 
    
    def task_delete(self, task, show_notification=True): 
        """Remove a task from the list."""
        self.tasks.controls.remove(task) 
        self.update() 
        self.save_tasks() 
        if show_notification: 
            self.page.snack_bar.content.value = f"❌ Task eliminated: {task.display_task.label}" 
            self.page.snack_bar.open = True 
            self.page.update() 

    def clear_clicked(self, e): 
        """Remove all completed tasks."""
        removed = 0 
        for task in self.tasks.controls[:]: 
            if task.completed: 
                self.task_delete(task, show_notification=False) 
                removed += 1 
        self.save_tasks() 

        if removed > 0: 
            self.page.snack_bar.content.value = f"🗑️ {removed} task(s) completed eliminated" 
            self.page.snack_bar.open = True 
            self.page.update() 

    def before_update(self): 
        """Update task visibility based on filter and count."""
        status = self.filter.tabs[self.filter.selected_index].text 
        count = 0 
        for task in self.tasks.controls: 
            task.visible = ( 
                status == "all" 
                or (status == "active" and not task.completed) 
                or (status == "completed" and task.completed) 
            ) 
            if not task.completed: 
                count +=1 
        self.items_left.value = f"{count} active item(s) left"  

    def tabs_changed(self, e): 
        """Handle tab selection changes."""
        self.update() 

    def save_tasks(self):
        data = []
        for task in self.tasks.controls:
            data.append({
                "name": task.display_task.label,
                "completed": task.completed,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
            })
        with open("tasks.json", "w") as f:
            json.dump(data, f, indent=2) 

    def load_tasks(self):
        if not os.path.exists("tasks.json"):
            return
        with open("tasks.json", "r") as f:
            data = json.load(f)
            for item in data:
                task = Task(
                    item["name"],
                    self.task_status_change,
                    self.task_delete,
                    created_at=item.get("created_at"),
                    completed_at=item.get("completed_at"),
                )
                task.completed = item["completed"]
                task.display_task.value = item["completed"]
                self.tasks.controls.append(task) 

    def export_tasks_csv(self, e=None):
        with open("tasks_export.csv", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Task", "Completed", "Created At", "Completed At"])

            for task in self.tasks.controls:
                writer.writerow([
                    task.display_task.label,
                    task.completed,
                    task.created_at.split(" ")[0] if task.created_at else "",
                    task.completed_at.split(" ")[0] if task.completed_at else ""
                ])

        self.page.snack_bar.content.value = "✅ Export complete"
        self.page.snack_bar.open = True
        self.page.update()

    def analyze_tasks_from_csv():
        tasks_by_date = defaultdict(lambda: {"completed": 0, "total": 0})

        with open("tasks_export.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row["Date"]
                tasks_by_date[date]["total"] += 1
                if row["Completed"].lower() == "true":
                    tasks_by_date[date]["completed"] += 1

        # Print results
        for date, stats in tasks_by_date.items():
            completed = stats["completed"]
            total = stats["total"]
            percent = (completed / total) * 100 if total else 0
            print(f"{date}: {completed}/{total} completed ({percent:.1f}%)")
        

# Main function that sets up the application page
def main(page: ft.Page): 
    page.title = "To-Do App" 
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 
    page.update() 
    todo = TodoApp(page) 
    page.add(todo) 

# Run the application
if __name__ == "__main__":
    ft.app(target=main)
