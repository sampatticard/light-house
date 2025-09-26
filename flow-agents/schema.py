class FormFillingStatus:
    def __init__(self):
        self.step_index = 0
        self.current_step_summary = ""
        self.awaiting_user_input = False
        self.requested_input_type = None
        self.task_complete = False
        self.otp = None
        self.captcha = None
        self.aadhaar_number = ""
        self.family_id = ""
        self.dob = ""
        self.phone = ""

    def to_dict(self):
        return {
            "step_index": self.step_index,
            "current_step_summary": self.current_step_summary,
            "awaiting_user_input": self.awaiting_user_input,
            "requested_input_type": self.requested_input_type,
            "task_complete": self.task_complete,
            "otp": self.otp,
            "captcha": self.captcha,
            "aadhaar_number": self.aadhaar_number,
            "family_id": self.family_id,
            "dob": self.dob,
            "phone": self.phone,
        }
