class BytesReader:
    def __init__(self, bytes_data):
        self.data = bytes_data
        self.offset = 0

    def read_uint8(self):
        value = self.data[self.offset]
        self.offset += 1
        return value

    def read_bytes(self, length):
        value = self.data[self.offset:self.offset + length]
        self.offset += length
        return value

    def read_uint32_be(self):
        # Read 4 bytes as an unsigned 32-bit integer (big-endian)
        value = int.from_bytes(self.read_bytes(4), byteorder='big', signed=False)
        return value
