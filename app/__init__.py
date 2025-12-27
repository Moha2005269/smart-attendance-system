def __init__(self):
    super().__init__()
    self.setWindowTitle("Smart Attendance System")
    self.setGeometry(300, 200, 450, 300)

    # Track logged-in user (from auth.py)
    self.current_user = None

    self.show_login_screen()
