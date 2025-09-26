class DocumentProcessor:
    """Advanced document processing utilities"""
    
    @staticmethod
    def preprocess_image_for_ocr(image_path: str) -> str:
        """Advanced image preprocessing for better OCR results"""
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Deskewing
        coords = np.column_stack(np.where(denoised > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        (h, w) = denoised.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(rotated)
        
        # Save preprocessed image
        preprocessed_path = image_path.replace('.', '_preprocessed.')
        cv.imwrite(preprocessed_path, enhanced)
        
        return preprocessed_path

    @staticmethod
    def extract_aadhaar_details(text: str) -> Dict[str, Any]:
        """Extract comprehensive Aadhaar card details"""
        details = {}
        
        # Aadhaar number
        aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
        aadhaar_match = re.search(aadhaar_pattern, text)
        if aadhaar_match:
            details['aadhaar_number'] = aadhaar_match.group().replace(' ', '')
        
        # Name (English)
        name_patterns = [
            r'Name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][A-Z\s]{2,}?)(?:\s*(?:S/O|D/O|W/O))',
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text)
            if name_match:
                details['name'] = name_match.group(1).strip()
                break
        
        # Father's/Spouse name
        father_patterns = [
            r'(?:S/O|Son of|Father)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:D/O|Daughter of)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:W/O|Wife of)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in father_patterns:
            father_match = re.search(pattern, text, re.IGNORECASE)
            if father_match:
                details['father_name'] = father_match.group(1).strip()
                break
        
        # Date of Birth
        dob_patterns = [
            r'DOB[:\s]*(\d{2}/\d{2}/\d{4})',
            r'Date of Birth[:\s]*(\d{2}/\d{2}/\d{4})',
            r'जन्म तिथि[:\s]*(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in dob_patterns:
            dob_match = re.search(pattern, text, re.IGNORECASE)
            if dob_match:
                details['date_of_birth'] = dob_match.group(1)
                break
        
        # Gender
        if re.search(r'\b(?:MALE|पुरुष)\b', text, re.IGNORECASE):
            details['gender'] = 'Male'
        elif re.search(r'\b(?:FEMALE|महिला)\b', text, re.IGNORECASE):
            details['gender'] = 'Female'
        
        # Address
        address_patterns = [
            r'Address[:\s]*([^\n]{20,})',
            r'पता[:\s]*([^\n]{20,})',
        ]
        
        for pattern in address_patterns:
            address_match = re.search(pattern, text, re.IGNORECASE)
            if address_match:
                details['address'] = address_match.group(1).strip()
                break
        
        return details

    @staticmethod
    def extract_pan_details(text: str) -> Dict[str, Any]:
        """Extract comprehensive PAN card details"""
        details = {}
        
        # PAN number
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        pan_match = re.search(pan_pattern, text)
        if pan_match:
            details['pan_number'] = pan_match.group()
        
        # Name
        name_patterns = [
            r'Name[:\s]*([A-Z][A-Z\s]{2,}?)(?:\s*Father)',
            r'([A-Z][A-Z\s]{10,}?)(?:\s*Father)',
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text)
            if name_match:
                details['name'] = name_match.group(1).strip()
                break
        
        # Father's name
        father_patterns = [
            r"Father's Name[:\s]*([A-Z][A-Z\s]{2,}?)(?:\s*Date|$)",
            r"Father[:\s]*([A-Z][A-Z\s]{2,}?)(?:\s*Date|$)",
        ]
        
        for pattern in father_patterns:
            father_match = re.search(pattern, text)
            if father_match:
                details['father_name'] = father_match.group(1).strip()
                break
        
        # Date of Birth
        dob_patterns = [
            r'Date of Birth[:\s]*(\d{2}/\d{2}/\d{4})',
            r'DOB[:\s]*(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in dob_patterns:
            dob_match = re.search(pattern, text)
            if dob_match:
                details['date_of_birth'] = dob_match.group(1)
                break
        
        return details

    @staticmethod
    def extract_bank_statement_details(text: str) -> Dict[str, Any]:
        """Extract bank statement details"""
        details = {}
        
        # Account number
        account_patterns = [
            r'Account\s+No[:\s]*(\d+)',
            r'A/c\s+No[:\s]*(\d+)',
            r'Account\s+Number[:\s]*(\d+)',
        ]
        
        for pattern in account_patterns:
            acc_match = re.search(pattern, text, re.IGNORECASE)
            if acc_match:
                details['account_number'] = acc_match.group(1).strip()
                break
        
        # IFSC code
        ifsc_pattern = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
        ifsc_match = re.search(ifsc_pattern, text)
        if ifsc_match:
            details['ifsc_code'] = ifsc_match.group()
        
        # Account holder name
        name_patterns = [
            r'Account\s+Holder[:\s]*([A-Z][A-Za-z\s]{2,}?)(?:\s*Account|\n)',
            r'Name[:\s]*([A-Z][A-Za-z\s]{2,}?)(?:\s*Account|\n)',
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.IGNORECASE)
            if name_match:
                details['account_holder_name'] = name_match.group(1).strip()
                break
        
        # Balance
        balance_patterns = [
            r'Balance[:\s]*(?:Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d{2})?)',
            r'Available\s+Balance[:\s]*(?:Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d{2})?)',
            r'Closing\s+Balance[:\s]*(?:Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d{2})?)',
        ]
        
        for pattern in balance_patterns:
            balance_match = re.search(pattern, text, re.IGNORECASE)
            if balance_match:
                details['balance'] = balance_match.group(1).replace(',', '')
                break
        
        # Statement period
        period_patterns = [
            r'Statement\s+Period[:\s]*(\d{2}/\d{2}/\d{4})\s*to\s*(\d{2}/\d{2}/\d{4})',
            r'From[:\s]*(\d{2}/\d{2}/\d{4})\s*To[:\s]*(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in period_patterns:
            period_match = re.search(pattern, text, re.IGNORECASE)
            if period_match:
                details['statement_from'] = period_match.group(1)
                details['statement_to'] = period_match.group(2)
                break
        
        return details


        