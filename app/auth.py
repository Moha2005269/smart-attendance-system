from tkinter import messagebox
from app.database import get_student

class AuthManager:

    def __init__(self):
        self.current_user = None

    def login(self, student_id, password):
        user = get_student(student_id, password)
        if user:
            self.current_user = {
                "id": user[0],
                "student_id": user[1],
                "name": user[2],
                "class_name": user[3]
            }
            return True
        else:
            return False

    def logout(self):
        self.current_user = None

    def is_logged_in(self):
        return self.current_user is not None

    def get_current_user(self):
        return self.current_user
