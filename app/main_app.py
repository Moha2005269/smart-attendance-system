import sys
import cv2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, 
    QDialog, QFormLayout, QMessageBox, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

# --- IMPORTS ---
from app.auth import AuthManager
from app import database
from app.models import Student, Staff  # <--- IMPORT STAFF HERE
from app.attendance import AttendanceManager

# --- REGISTER DIALOG (Updated for Staff) ---
class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New User")
        self.setMinimumWidth(300)
        
        # Layout
        layout = QFormLayout(self)
        
        # Fields
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        
        # Dynamic Field (Class vs Department)
        self.extra_input = QLineEdit()
        self.extra_input.setPlaceholderText("Class Name (e.g., CS-101)")

        # Checkbox to switch roles
        self.staff_check = QCheckBox("Register as Staff Member")
        self.staff_check.toggled.connect(self.toggle_role)

        save_btn = QPushButton("Save User")
        save_btn.clicked.connect(self.save_user)

        layout.addRow("Name:", self.name_input)
        layout.addRow("User ID:", self.id_input)
        layout.addRow("Password:", self.pass_input)
        layout.addRow(self.staff_check)
        layout.addRow("Class/Dept:", self.extra_input)
        layout.addRow(save_btn)

    def toggle_role(self, checked):
        """Switches the label based on checkbox state"""
        if checked:
            self.extra_input.setPlaceholderText("Department (e.g., IT Dept)")
        else:
            self.extra_input.setPlaceholderText("Class Name (e.g., CS-101)")

    def save_user(self):
        name = self.name_input.text()
        uid = self.id_input.text()
        pwd = self.pass_input.text()
        extra = self.extra_input.text()

        if not name or not uid or not pwd:
            QMessageBox.warning(self, "Error", "Fill all fields")
            return

        # --- POLYMORPHISM IN ACTION ---
        if self.staff_check.isChecked():
            # Create STAFF Object
            new_user = Staff(name, uid, extra, pwd)
        else:
            # Create STUDENT Object
            new_user = Student(name, uid, pwd, extra)

        # Both classes have .save_to_db(), but they behave differently
        if new_user.save_to_db():
            role = new_user.get_role()
            QMessageBox.information(self, "Success", f"{role} {name} registered!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "ID exists or DB Error")

# --- MAIN APPLICATION (Same as before) ---
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Attendance System")
        self.setGeometry(100, 100, 900, 600)
        
        self.auth_manager = AuthManager()
        self.attendance_manager = AttendanceManager()
        database.init_db()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.show_login_screen()

    def clear_window(self):
        if self.timer.isActive():
            self.timer.stop()
        self.attendance_manager.stop_camera()
        
        if self.centralWidget():
            self.centralWidget().deleteLater()

    # --- LOGIN SCREEN ---
    def show_login_screen(self):
        self.clear_window()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        
        title = QLabel("SMART ATTENDANCE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:24px; font-weight:bold; color: #007ACC;")

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("User ID")
        self.student_id_input.setStyleSheet("padding: 10px;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("padding: 10px;")

        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("background-color: #007ACC; color: white; padding: 10px; font-weight: bold;")
        login_btn.clicked.connect(self.login_clicked)

        reg_btn = QPushButton("Register New User")
        reg_btn.setStyleSheet("color: #007ACC; background: transparent; border: none;")
        reg_btn.clicked.connect(self.open_register)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.student_id_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        layout.addWidget(reg_btn)
        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def login_clicked(self):
        sid = self.student_id_input.text()
        pwd = self.password_input.text()

        if self.auth_manager.login(sid, pwd):
            user = self.auth_manager.get_current_user()
            self.show_main_screen(user)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid ID or Password")

    def open_register(self):
        dlg = RegisterDialog(self)
        dlg.exec()

    # --- MAIN DASHBOARD SCREEN ---
    def show_main_screen(self, user):
        self.clear_window()
        
        main_layout = QHBoxLayout()

        # --- LEFT PANEL: CAMERA ---
        left_panel = QVBoxLayout()
        
        welcome_label = QLabel(f"Welcome, {user.name}")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.video_label = QLabel("Camera Offline")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; border-radius: 10px;")
        self.video_label.setMinimumSize(480, 360)
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.clicked.connect(self.toggle_camera)
        
        self.mark_btn = QPushButton("Mark Attendance")
        self.mark_btn.clicked.connect(self.mark_attendance)
        self.mark_btn.setEnabled(False)

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        logout_btn.clicked.connect(self.logout_clicked)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.mark_btn)

        left_panel.addWidget(welcome_label)
        left_panel.addWidget(self.video_label)
        left_panel.addWidget(self.status_label)
        left_panel.addLayout(btn_layout)
        left_panel.addWidget(logout_btn)
        left_panel.addStretch()

        # --- RIGHT PANEL: HISTORY ---
        right_panel = QVBoxLayout()
        
        hist_title = QLabel("Attendance History")
        hist_title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")
        self.search_bar.textChanged.connect(self.filter_history)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_content = QLabel("Loading...")
        self.history_content.setAlignment(Qt.AlignTop)
        self.history_content.setStyleSheet("padding: 10px;")
        self.history_scroll.setWidget(self.history_content)

        right_panel.addWidget(hist_title)
        right_panel.addWidget(self.search_bar)
        right_panel.addWidget(self.history_scroll)

        main_layout.addLayout(left_panel, 65)
        main_layout.addLayout(right_panel, 35)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.refresh_history()

    # --- CAMERA LOGIC ---
    def toggle_camera(self):
        if not self.timer.isActive():
            self.attendance_manager.start_camera()
            self.timer.start(30)
            self.start_btn.setText("Stop Camera")
            self.mark_btn.setEnabled(True)
            self.status_label.setText("Status: Camera Active")
        else:
            self.timer.stop()
            self.attendance_manager.stop_camera()
            self.video_label.setPixmap(QPixmap())
            self.video_label.setText("Camera Offline")
            self.start_btn.setText("Start Camera")
            self.mark_btn.setEnabled(False)
            self.status_label.setText("Status: Ready")

    def update_frame(self):
        cap = self.attendance_manager.cap
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                scaled_pixmap = QPixmap.fromImage(q_img).scaled(
                    self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)

    def mark_attendance(self):
        user = self.auth_manager.get_current_user()
        if not user: return

        self.timer.stop()
        self.status_label.setText("Status: Scanning Face...")
        QApplication.processEvents()

        success, msg = self.attendance_manager.detect_and_mark(
            student_id=user.get_id(),
            student_name=user.name
        )

        if success:
            self.status_label.setText(f"✅ {msg}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.refresh_history()
        else:
            self.status_label.setText(f"❌ {msg}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

        self.timer.start(30)

    def logout_clicked(self):
        self.auth_manager.logout()
        self.show_login_screen()

    # --- HISTORY LOGIC ---
    def refresh_history(self):
        self.filter_history("")

    def filter_history(self, search_text):
        user = self.auth_manager.get_current_user()
        if not user: return

        records = database.get_attendance_history(user.get_id())
        
        if not records:
            self.history_content.setText("No records found.")
            return

        display_text = ""
        for row in records:
            timestamp = str(row[0])
            status = "Late" if row[4] else "Present"
            confidence = f"{row[3]:.0f}%" if row[3] else "N/A"
            line = f"[{timestamp}] {status} (Conf: {confidence})"

            if search_text.lower() in line.lower():
                display_text += line + "\n\n"

        self.history_content.setText(display_text if display_text else "No matching records.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
