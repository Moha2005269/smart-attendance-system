# app/models.py
from app.database import add_student

# 1. BASE CLASS (Requirement: Base/Super Class)
class Person:
    def __init__(self, name, user_id):
        self.name = name
        # 2. ENCAPSULATION (Requirement: Private Attribute)
        self.__user_id = user_id 

    def get_id(self):
        """Getter for private ID"""
        return self.__user_id

    # 3. POLYMORPHISM (Base method)
    def get_role(self):
        return "General User"

    def save_to_db(self):
        raise NotImplementedError("Subclasses must implement save_to_db")

# 4. DERIVED CLASS (Requirement: Sub Class 1)
class Student(Person):
    def __init__(self, name, user_id, password, class_name):
        super().__init__(name, user_id)
        self.password = password
        self.class_name = class_name

    # POLYMORPHISM (Overridden method)
    def get_role(self):
        return "Student"

    def save_to_db(self):
        # Calls the function in database.py
        return add_student(self.get_id(), self.password, self.name, self.class_name)

# 5. DERIVED CLASS (Requirement: Sub Class 2)
class Staff(Person):
    def __init__(self, name, user_id, department):
        super().__init__(name, user_id)
        self.department = department

    def get_role(self):
        return "Staff"

    def save_to_db(self):
        print(f"Mock saving Staff {self.name}...")
        return True
