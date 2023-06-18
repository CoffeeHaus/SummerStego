from PIL import Image
import sys

class PatternSteg:
    InputFile = "test.bmp"
    OutputFile = "output.bmp"
    DataFile = "testfile.txt"
    StartCrib = "101000000101"
    EndCrib = "101111111101"
    data = []
    def encode(self):
        img = Image.open(self.InputFile)
        # Load the image into memory to allow pixel access.
        pixels = img.load()
        bin = self.file_to_binary()
        data = bin
        while (len(data) % 3 != 0):
            data += '0'
        data = self.StartCrib + bin + self.EndCrib
        res = [data[i:i + 3] for i in range(0, len(data), 3)]
        while len(res[-1]) < 3:
            res[-1] += "0"

        print("data to be encoded")
        print(res)
        i = 0
        while not (i >= len(res)):
            # Go over each pixel.
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b = pixels[x, y]
                    changed = False
                    # R
                    if (i < len(res) and self.check_if_data(res[i], r)):
                        r = r | 1
                        i += 1
                        changed = True
                        if (i >= len(res)):
                            print("BREAK")
                            break

                    else:
                        r = r & 254
                    # G
                    if (i < len(res) and self.check_if_data(res[i], g)):
                        g = g | 1
                        i += 1
                        changed = True
                        if (i >= len(res)):
                            print("BREAK")
                            break

                    else:
                        g = g & 254

                    # B
                    if (i < len(res) and self.check_if_data(res[i], b)):
                        b = b | 1
                        i += 1
                        changed = True
                        if (i >= len(res)):
                            print("BREAK")
                            break
                    else:
                        b = b & 254

                    # Update the pixel with modified values.
                    pixels[x, y] = (r, g, b)

        # Save the modified image.
        img.save(self.OutputFile)

    def file_to_binary(self):
        binary_content = ""

        try:
            with open(self.DataFile, 'rb') as file:
                while (byte := file.read(1)):
                    binary_content += f'{byte[0]:08b}'
        except FileNotFoundError:
            print("The file does not exist")
            return

        return binary_content

    def to_bin(self, data):
        return "{0:b}".format(data)

    def check_if_data(value, data):
        # print(value,data)
        tempv = int(value, 2)
        temp = int(data)
        temp = temp & 14
        temp = temp >> 1
        # print(temp,tempv)
        if temp == tempv:
            return True
        else:
            return False

    def CheckForCrib(self):
        if (len(self.data) > 4):
            check = True
            z = len(self.data) - 1
            if (self.data[z] == 5):
                check = False
            if (self.data[z - 1] == 7):
                check = False
            if (self.data[z - 2] == 7):
                check = False
            if (self.data[z - 3] == 5):
                check = False
            return check

    def decode(self):
        img = Image.open(self.OutputFile)
        # Load the image into memory to allow pixel access.
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]

                # R
                if (r & 1 == 1):
                    bitdata = (r >> 1) & 7
                    if self.CheckForCrib():
                        return
                    self.data.append(self.to_bin(bitdata))

                # G
                if (g & 1 == 1):
                    bitdata = (g >> 1) & 7
                    if self.CheckForCrib():
                        return
                    self.data.append(self.to_bin(bitdata))
                # B
                if (b & 1 == 1):
                    data = (b >> 1) & 7
                    if self.CheckForCrib():
                        return
                    self.data.append(self.to_bin(bitdata))

                if (len(self.data) == 4):
                    pass

        fdat = ""
        for x in data[4:-4]:
            while len(x) != 3:
                x = '0' + x
            fdat += x
        #print(fdat)
        byte_data = bytes(int(fdat[i:i + 8], 2) for i in range(0, len(fdat), 8))
        with open("dataoutput.txt", "wb") as binary_file:
            binary_file.write(byte_data)


pat = PatternSteg()
if (sys.argv[1] == "-e"):
    pat.encode()
elif (sys.argv[1] == "-d"):
    pat.decode()
