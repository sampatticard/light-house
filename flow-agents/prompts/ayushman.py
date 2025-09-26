from baml_client import types
from baml_client import b
def get_ayushman_form_filling_prompt(form_data, current_status):
    status_obj = types.FormFillingStatus(**current_status)

    baml_params = dict(
        task_steps="Ayushman Bharat Card Registration",
        current_status=status_obj,
        phone=form_data.get('phone', "9330575742"),
        aadhaar_number=form_data.get('aadhaar_number', "123412341234"),
        aadhar_otp=form_data.get('aadhar_otp'),
        dob=form_data.get('dob', "1950-01-01"),
        relationship=form_data.get('relationship', "Self"),
        pin_code=form_data.get('pin_code', "110001"),
        district=form_data.get('district', "New Delhi"),
        sub_district=form_data.get('sub_district', "Chanakyapuri"),
        village=form_data.get('village', "VillageName"),
        area_type=form_data.get('area_type', "Urban"),
        family_id=form_data.get('family_id', "FAM123")
    )

    # ✅ Use the imported FormFilling class directly
    return b.FormFilling(**baml_params)
