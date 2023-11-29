from PyQt6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from models.task_manager import TaskManager
from PyQt6.QtGui import QIcon

class StatisticsDialog(QDialog):
    def __init__(self, task_manager: TaskManager, user_id: int, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.user_id = user_id

        self.setWindowTitle("Statistics")
        self.setGeometry(100, 100, 800, 600)

        # Load the icon
        self.setWindowIcon(QIcon('resources/favicon.ico'))

        # Initialize the layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create the matplotlib Figure and Canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.draw_charts()

    def draw_charts(self):
        # Retrieve the statistics from the task manager
        task_data = self.task_manager.get_task_statistics(self.user_id)

        # Clear any existing figures
        self.figure.clf()

        # Create a GridSpec layout within the figure
        gs = gridspec.GridSpec(2, 2, height_ratios=[2, 2])

        # Create subplots using the GridSpec layout
        # Span the first row completely for the pie chart
        ax1 = self.figure.add_subplot(gs[0, :])
        # Second row, first column for the bar chart
        ax2 = self.figure.add_subplot(gs[1, 0])
        # Second row, second column for the line chart
        ax3 = self.figure.add_subplot(gs[1, 1])

        # Validate data and draw the "Tasks by Status" pie chart
        if 'status' in task_data and task_data['status']:
            status_data = task_data['status']
            status_labels = ['Incomplete' if d['status']
                            == 1 else 'Complete' for d in status_data]
            status_values = [d['count'] for d in status_data]
            ax1.pie(status_values, labels=status_labels, autopct='%1.1f%%')
            ax1.set_title('Tasks by Status')

        # Validate data and draw the "Tasks by Category" bar chart
        if 'category' in task_data and task_data['category']:
            category_data = task_data['category']
            categories = [d['category'] for d in category_data]
            category_counts = [d['count'] for d in category_data]
            ax2.bar(range(len(categories)), category_counts, tick_label=categories)
            ax2.set_title('Tasks by Category')
            ax2.set_xticklabels(categories, rotation=45)

        # Validate data and draw the "Tasks by Due Date" line chart
        if 'due_date' in task_data and task_data['due_date']:
            due_date_data = task_data['due_date']
            dates = [d['due_date'] for d in due_date_data]
            counts = [d['count'] for d in due_date_data]
            ax3.plot(dates, counts, marker='o', linestyle='-')
            ax3.set_title('Tasks by Date')
            ax3.tick_params(axis='x', rotation=45)

        # Adjust layout to prevent overlapping
        self.figure.autofmt_xdate()  # Automatic adjustment for date labels

        # Refresh the canvas
        self.canvas.draw()
