from PIL import Image
import sys
import argparse
verbose = True


def verbose(string):
    global verbose
    if verbose:
        print(string)


def to_bin(data):
    return "{0:b}".format(data)


class PatternSteg:
    InputFile = "test.bmp"
    OutputFile = "output.bmp"
    DataFile = "testfile.txt"
    DataOutputFile = "dataout.txt"
    StartCrib = "101000000101"
    EndCrib = "101111111101"
    EncodingLength = 3
    data = []

    def encode(self):
        img = Image.open(self.InputFile)
        # Load the image into memory to allow pixel access.
        pixels = img.load()
        data = self.file_to_binary()
        while len(data) % self.EncodingLength != 0:
            data += '0'
        data = self.StartCrib + data + self.EndCrib
        bytesEncoded = [data[i:i + self.EncodingLength] for i in range(0, len(data), self.EncodingLength)]

        # pads enough zeros to make groups of three bytes
        while len(bytesEncoded[-1]) < self.EncodingLength:
            bytesEncoded[-1] += "0"

        verbose("data to be encoded")
        verbose(bytesEncoded)
        data_count = 0
        bits_changed = 0
        lastx = 0
        lasty = 0
        test = img.getbands()
        if 'P' in test:
            palette = img.getpalette()
            for x in range(img.width):
                for y in range(img.height):
                    index = img.getpixel((x, y))  # index in the palette
                    base = 3 * index  # because each palette color has 3 components
                    r, g, b = palette[base:base + 3]
                    if_changed = False
                    data_added = []
                    val = [r, g, b]

                    for i, s in enumerate(val):  # enumerates through R G B
                        if not data_count < len(bytesEncoded):  # DoneEncoding Data
                            break
                        elif self.check_if_data(bytesEncoded[data_count], s):  # if data is a match

                            if (s & 1) == 0:  # mark this data as encoded
                                s = s | 1
                                bits_changed += 1
                            data_added.append(bytesEncoded[data_count])
                            s = s | 1
                            lastx = x
                            lasty = y
                            data_count += 1
                            if_changed = True

                        else:  # data not a match
                            if (s & 1) == 1:  # mark this data as encoded
                                s = s & 254
                                bits_changed += 1
                        val[i] = s

                    if if_changed:
                        verbose("Pixel [{},{}] added {}".format(x, y, data_added))

                        # Update the pixel with modified values.
                        r, g, b = val
                        palette[base] = r
                        palette[base + 1] = g
                        palette[base + 2] = b
            img.putpalette(palette)
        else:
            while data_count < len(bytesEncoded):
                # Go over each pixel.
                for x in range(img.width):
                    for y in range(img.height):
                        #each pixel
                        r, g, b = pixels[x, y]
                        if_changed = False
                        data_added = []
                        val = [r, g, b]

                        for i, s in enumerate(val):  # enumerates through R G B
                            if not data_count < len(bytesEncoded):  # DoneEncoding Data
                                break
                            elif self.check_if_data(bytesEncoded[data_count], s):  # if data is a match

                                if (s & 1) == 0:  # mark this data as encoded
                                    s = s | 1
                                    bits_changed += 1
                                data_added.append(bytesEncoded[data_count])
                                s = s | 1
                                lastx = x
                                lasty = y
                                data_count += 1
                                if_changed = True

                            else:  # data not a match
                                if (s & 1) == 1:  # mark this data as encoded
                                    s = s & 254
                                    bits_changed += 1
                            val[i] = s

                        if if_changed:
                            verbose("Pixel [{},{}] added {}".format(x, y, data_added))
                        # Update the pixel with modified values.
                        r, g, b = val
                        pixels[x, y] = (r, g, b)


        # Save the modified image.
        img.save(self.OutputFile)
        verbose("Last Pixel modified [{},{}]".format(lastx, lasty))
        verbose("Bits changed {} Bits saved {}".format(bits_changed, len(bytesEncoded) * 3))

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

    def check_if_data(self, value, data):
        # print(value,data)
        mask = 0
        if self.EncodingLength == 3:
            mask = 14
        elif self.EncodingLength == 2:
            mask = 6
        tempv = int(value, 2)
        temp = int(data)
        temp = temp & mask
        temp = temp >> 1
        # print(temp,tempv)
        if temp == tempv:
            return True
        else:
            return False

    def check_for_crib(self):
        if len(self.data) > 4:
            check = True
            z = len(self.data) - 1
            test = int(self.data[z], 2)

            if not (int(self.data[z], 2) == 5):
                check = False
            if not (int(self.data[z - 1], 2) == 7):
                check = False
            if not (int(self.data[z - 2], 2) == 7):
                check = False
            if not (int(self.data[z - 3], 2) == 5):
                check = False
            return check

    def decode(self):
        img = Image.open(self.OutputFile)
        # Load the image into memory to allow pixel access.
        pixels = img.load()
        test = img.getbands()
        if 'P' in test:
            palette = img.getpalette()
            for x in range(img.width):
                for y in range(img.height):
                    index = img.getpixel((x, y))  # index in the palette
                    base = 3 * index  # because each palette color has 3 components
                    r, g, b = palette[base:base + 3]
                    # R
                    if (r & 1) == 1:
                        bitdata = (r >> 1) & 7
                        if self.check_for_crib():
                            return
                        self.data.append(to_bin(bitdata))
                    # G
                    if (g & 1) == 1:
                        bitdata = (g >> 1) & 7
                        if self.check_for_crib():
                            return
                        self.data.append(to_bin(bitdata))
                    # B
                    if (b & 1) == 1:
                        bitdata = (b >> 1) & 7
                        if self.check_for_crib():
                            return
                        self.data.append(to_bin(bitdata))

                    # Update the pixel with modified values.
                    r, g, b = palette[base:base + 3]
                    palette[base] = r
                    palette[base + 1] = g
                    palette[base + 2] = b
        else:
            for x in range(img.width):
                for y in range(img.height):
                    r, g, b = pixels[x, y]

                    # R
                    if (r & 1) == 1:
                        bitdata = (r >> 1) & 7
                        if self.check_for_crib():
                            break
                        self.data.append(to_bin(bitdata))

                    # G
                    if (g & 1) == 1:
                        bitdata = (g >> 1) & 7
                        if self.check_for_crib():
                            break
                        self.data.append(to_bin(bitdata))
                    # B
                    if (b & 1) == 1:
                        bitdata = (b >> 1) & 7
                        if self.check_for_crib():
                            break
                        self.data.append(to_bin(bitdata))

                    if len(self.data) == 4:
                        print(self.data)

        fdat = ""
        for x in self.data[4:-4]:
            while len(x) != 3:
                x = '0' + x
            fdat += x
        print(fdat)
        byte_data = bytes(int(fdat[i:i + 8], 2) for i in range(0, len(fdat), 8))
        with open(self.DataOutputFile, "wb") as binary_file:
            binary_file.write(byte_data)


def parse_args():
    parser = argparse.ArgumentParser(description="Example Argument Parser")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encode", type=str, help="Specify the file to encode")
    group.add_argument("-d", "--decode", type=str, help="Specify the file to decode")
    args = parser.parse_args()

    return args


def main():
    pat = PatternSteg()
    args = parse_args()
    if args.encode:
        pat.encode()
    elif args.decode:
        pat.decode()


main()
