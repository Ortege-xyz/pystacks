from enum import Enum
from bytes_reader import BytesReader

class ClarityType(Enum):
    INT = 0
    UINT = 1
    BUFFER = 2
    BOOL_TRUE = 3
    BOOL_FALSE = 4
    PRINCIPAL_STANDARD = 5
    PRINCIPAL_CONTRACT = 6
    RESPONSE_OK = 7
    RESPONSE_ERR = 8
    OPTIONAL_NONE = 9
    OPTIONAL_SOME = 10
    LIST = 11
    TUPLE = 12
    STRING_ASCII = 13
    STRING_UTF8 = 14

class ClarityValue:
    def __init__(self, clarity_type):
        self.clarity_type = clarity_type

class ClarityBool(ClarityValue):
    def __init__(self, value):
        super().__init__(ClarityType.BOOL_TRUE if value else ClarityType.BOOL_FALSE)
        self.value = value

class ClarityInt(ClarityValue):
    def __init__(self, value):
        super().__init__(ClarityType.INT)
        self.value = value

class ClarityUInt(ClarityValue):
    def __init__(self, value):
        super().__init__(ClarityType.UINT)
        self.value = value

def deserialize_cv(serialized_value):
    if isinstance(serialized_value, str):
        if serialized_value.startswith('0x'):
            serialized_value = bytes.fromhex(serialized_value[2:])
        else:
            serialized_value = bytes.fromhex(serialized_value)
    elif isinstance(serialized_value, bytes):
        pass
    else:
        raise ValueError("Invalid serialized value type")

    reader = BytesReader(serialized_value)
    clarity_type = reader.read_uint8()

    if clarity_type == ClarityType.INT.value:
        return deserialize_int_cv(reader)
    elif clarity_type == ClarityType.UINT.value:
        return deserialize_uint_cv(reader)
    elif clarity_type == ClarityType.BOOL_TRUE.value:
        return ClarityBool(True)
    elif clarity_type == ClarityType.BOOL_FALSE.value:
        return ClarityBool(False)
    elif clarity_type == ClarityType.OPTIONAL_SOME.value:
        return deserialize_cv(reader.read_bytes(reader.read_uint32_be()))
    elif clarity_type == ClarityType.OPTIONAL_NONE.value:
        return None
    else:
        raise ValueError(f"Unknown Clarity type: {clarity_type}")

def deserialize_int_cv(reader):
    value = reader.read_bytes(16)
    return ClarityInt(int.from_bytes(value, byteorder='big', signed=True))

def deserialize_uint_cv(reader):
    value = reader.read_bytes(16)
    return ClarityUInt(int.from_bytes(value, byteorder='big', signed=False))
