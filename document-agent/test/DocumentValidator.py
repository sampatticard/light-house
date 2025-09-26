class DocumentValidator:
    """Advanced document validation utilities"""
    
    @staticmethod
    def validate_aadhaar_checksum(aadhaar_number: str) -> bool:
        """Validate Aadhaar number using Verhoeff algorithm"""
        if len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            return False
        
        # Verhoeff algorithm implementation
        multiplication_table = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        
        permutation_table = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        
        check = 0
        for i, digit in enumerate(reversed(aadhaar_number)):
            check = multiplication_table[check][permutation_table[i % 8][int(digit)]]
        
        return check == 0
    
    @staticmethod
    def validate_pan_checksum(pan_number: str) -> bool:
        """Validate PAN number format and structure"""
        if len(pan_number) != 10:
            return False
        
        # Check format: AAAPL1234C
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}'
        if not re.match(pattern, pan_number):
            return False
        
        # Fourth character should be 'P' for individual PAN
        if pan_number[3] not in ['P', 'F', 'A', 'T', 'B', 'C', 'G', 'H', 'L', 'J']:
            return False
        
        return True
    
    @staticmethod
    def validate_ifsc_code(ifsc_code: str) -> bool:
        """Validate IFSC code format"""
        if len(ifsc_code) != 11:
            return False
        
        # Format: ABCD0123456 (first 4 alpha, 5th is 0, last 6 alphanumeric)
        pattern = r'^[A-Z]{4}0[A-Z0-9]{6}'
        return bool(re.match(pattern, ifsc_code))