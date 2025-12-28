from app.database import add_student

# 1. BASE CLASS
class Person:
    def __init__(self, name, user_id):
        self.name = name
        # Encapsulation: Private attribute
        self.__user_id = user_id 

    def get_id(self):
        return self.__user_id

    def get_role(self):
        return "General User"

    def save_to_db(self):
        raise NotImplementedError("Subclasses must implement save_to_db")

# 2. DERIVED CLASS (Student)
class Student(Person):
    def __init__(self, name, user_id, password, class_name):
        super().__init__(name, user_id)
        self.password = password
        self.class_name = class_name

    def get_role(self):
        return "Student"

    def save_to_db(self):
        # Saves to the 'students' table
        return add_student(self.get_id(), self.password, self.name, self.class_name)

# 3. DERIVED CLASS (Staff) - NOW FUNCTIONAL
class Staff(Person):
    def __init__(self, name, user_id, department, password):
        super().__init__(name, user_id)
        self.department = department
        self.password = password

    def get_role(self):
        return "Staff"

    def save_to_db(self):
        # We reuse the existing 'students' table logic to save Staff
        # We treat 'department' as the 'class_name' in the DB to keep it simple
        return add_student(self.get_id(), self.password, self.name, self.department)
