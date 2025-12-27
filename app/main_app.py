import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit
)
from PySide6.QtCore import Qt
from app import auth
from app import database


class MainApp(QMainWindow):
    """
    Smart Attendance System
    Login Screen
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Attendance System")
        self.setGeometry(300, 200, 450, 300)
        self.show_login_screen()

    def clear_window(self):
        widget = QWidget()
        self.setCentralWidget(widget)

    def show_login_screen(self):
        """Login UI"""
        self.clear_window()

        layout = QVBoxLayout()

        title = QLabel("SMART ATTENDANCE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:bold;")

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Student ID")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login_clicked)

        layout.addWidget(title)
        layout.addWidget(self.student_id_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)




    def show_main_screen(self, student_id):
        """Main attendance screen UI"""
        self.clear_window()

        # Main horizontal layout
        main_layout = QVBoxLayout()

        # Welcome label
        welcome_label = QLabel(f"Welcome, {student_id}")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size:16px; font-weight:bold;")

        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Buttons
        start_btn = QPushButton("Start Attendance")
        start_btn.clicked.connect(self.start_attendance)

        mark_btn = QPushButton("Mark Attendance")
        mark_btn.clicked.connect(self.mark_attendance)

        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_clicked)

        # Attendance history (simple for now)
        history_label = QLabel("Attendance History")
        history_label.setStyleSheet("font-weight:bold;")

        self.history_box = QLabel("No attendance records yet.")
        self.history_box.setAlignment(Qt.AlignTop)
        self.history_box.setStyleSheet("border:1px solid gray; padding:5px;")

        # Add widgets to layout
        main_layout.addWidget(welcome_label)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(start_btn)
        main_layout.addWidget(mark_btn)
        main_layout.addWidget(history_label)
        main_layout.addWidget(self.history_box)
        main_layout.addWidget(logout_btn)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    

    def login_clicked(self):
        student_id = self.student_id_input.text()
        password = self.password_input.text()

        user = auth.login(student_id, password)

        if user is None:
            self.setWindowTitle("Login failed")
            return
        
        self.current_user = user
        self.show_main_screen(user["student_id"])

    def logout_clicked(self):
        auth.logout()
        self.current_user = None
        self.show_login_screen()

    def start_attendance(self):
        """Mock start attendance"""
        self.status_label.setText("Status: Detecting...")


    def mark_attendance(self):
        if not self.current_user:
            self.status_label.setText("Status: No user logged in")
            return
        
        user_id = self.current_user["id"]

        # Placeholder values (until recognizer is integrated)
        status = "Present"
        confidence = 0.0
        liveness_ok = True
        snapshot_path = None

        database.record_attendance(
            user_id,
            status,
            confidence,
            liveness_ok,
            snapshot_path
        )
        self.status_label.setText("Status: Attendance Recorded")

        self.history_box.setText(
            self.history_box.text()
            + f"\nAttendance recorded for {self.current_user['student_id']}"
        )
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
