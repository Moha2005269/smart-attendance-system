# app/auth.py
from app.database import get_student
from app.models import Student  # Import the Class

class AuthManager:
    def __init__(self):
        self.current_user = None

    def login(self, student_id, password):
        # 1. Get raw data from DB
        user_data = get_student(student_id, password)
        
        if user_data:
            # user_data = (db_id, student_id, name, class_name)
            
            # 2. Create STUDENT OBJECT (Satisfies "OOP Usage")
            self.current_user = Student(
                name=user_data[2],
                user_id=user_data[1],
                password=password, 
                class_name=user_data[3]
            )
            return True
        else:
            return False

    def logout(self):
        self.current_user = None

    def get_current_user(self):
        return self.current_user
