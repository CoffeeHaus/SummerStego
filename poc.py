from PIL import Image
import sys
import argparse
from enum import Enum
verbose = False


def verbose(string):
    global verbose
    if verbose:
        print(string)

class Position(Enum):
    bottomleft = 0
    bottomright = 1
    topright = 2
    topleft = 3
    middle = 4

class Direction(Enum):
    rowbyrow = 0
    #rowbyrowsnake = 1
    rowbyrowreverse = 2
    columnbycolumn = 3
    #columnbycolumnsnake = 4
    columnbycolumnreverse = 5
    #clockwisespiral = 6
    #counterclockwisespiral = 7

class PatternSteg:
    LoadedImage = None
    InputImageFile = "test.bmp"
    OutputImageFile = "output.bmp"
    DataFile = "testfile.txt"
    DataOutputFile = "dataout.txt"
    StartCrib = "101000000101"
    EndCrib = "101111111101"
    ImageHeight = 0
    ImageWidth = 0
    EncodingLength = 3
    data = []
    EncodingData = []
    StartingPosition = Position.bottomleft
    StartingDirection = Direction.rowbyrow
    OriginalData = None
    Palette = None
    Pixels = None


    def to_bin(data):
        return "{0:b}".format(data)

    def get_crib(self, encoding):
        if encoding == 4:
            return ('1001','0000','0000','1001')
        elif encoding == 3:
            return ('101', '000', '000', '000', '101')
        elif encoding == 2:
            return ('1001','0000','0000','1001')


    def set_data_file(self):
        pass

    def set_input_image_file(self):
        pass

    def set_output_image_file(self):
        pass

    def set_data_output_file(self):
        pass
    def get_pixel_position(self, starting_point, direction):
        starting_x, starting_y = starting_point
        #starts at point which is bottom left
        if direction == Direction.rowbyrow:
            for y in range(starting_y, self.ImageHeight):
                for x in range(starting_x, self.ImageWidth):
                    yield x, y
                starting_x = 0

        elif direction == Direction.columnbycolumn:
            for x in range(starting_x, self.ImageWidth):
                for y in range(starting_y, self.ImageHeight):
                    yield x, y
                starting_y = 0

        #starts at point which is bottom left
        if direction == Direction.rowbyrowreverse:
            for y in range(starting_y, self.ImageHeight):
                for x in range(starting_x, -1, -1):
                    yield x, y
                starting_x = self.ImageWidth -1

        elif direction == Direction.columnbycolumnreverse:
            for x in range(starting_x, self.ImageWidth):
                for y in range(starting_y, -1, -1):
                    yield x, y
                starting_y = self.ImageHeight -1

    def get_possible_starting_point(self):
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):

                r, g, b = self.get_rgb((x,y))
                val = (r,g,b)
                if_val = False
                for i, s in enumerate(val):
                    if self.check_if_data('1001', s) and self.EncodingLength == 4:
                        if_val = True
                    elif self.check_if_data('101', s) and self.EncodingLength == 3:
                        if_val = True
                    elif self.check_if_data('10', s) and self.EncodingLength == 2:
                        if_val = True
                    if if_val:
                        if_val = False
                        yield x,y
    def set_encoding_data(self, length):
        if length == 4:
            self.StartCrib = '1001000000001001'
            self.StartCrib = '1001111111111001'
        if length == 3:
            self.StartCrib = '101000000000101'
            self.StartCrib = '101111111111101'
        elif length == 2:
            self.StartCrib = '1001000000001001'
            self.StartCrib = '1001111111111001'

        self.EncodingLength = length
        data = self.OriginalData
        while len(data) % self.EncodingLength != 0:
            data += '0'
        data = self.StartCrib + data + self.EndCrib
        self.EncodingData = [data[i:i + self.EncodingLength] for i in range(0, len(data), self.EncodingLength)]


    def encode (self):
        self.OriginalData = self.file_to_binary()
        self.LoadedImage = Image.open(self.InputImageFile)
        # Load the image into memory to allow pixel access.
        self.ImageWidth = self.LoadedImage.width
        self.ImageHeight = self.LoadedImage.height

        if self.LoadedImage.getbands() == 'P':
            self.Palette = self.LoadedImage.getpalette()
        else:
            self.Pixels = self.LoadedImage.load()

        isFound = False
        for x in (100,50,20,10,5,3,2,1):
            best_case = self.test_encode(x)
            if best_case:
                point, direction, encoding, bits = best_case
                self.encode_data(point, direction, encoding)
                break


    def get_rgb(self, point):

        if self.Palette :
            index = self.LoadedImage.getpixel(point)  # index in the palette
            base = 3 * index  # because each palette color has 3 components
            return self.Palette[base:base + 3]
        else:
            return  self.Pixels[point]

    def set_rgb(self, point, rgb):
        if self.Palette:
            index = self.LoadedImage.getpixel(point)  # index in the palette
            base = 3 * index  # because each palette color has 3 components

            self.Palette[base] = rgb[0]
            self.Palette[base + 1] = rgb[1]
            self.Palette[base + 2] = rgb[2]
        else:
            self.Pixels[point] = rgb

    def test_encode(self, percentage_cutoff):
        possible = []
        is_found = False



        Outcomes = []
        bits_changed = 0
        possible_directions = []
        for e in (4, 3, 2):


            self.set_encoding_data(4)
            # data_excess is the factor of amount of bits that can be changed per actual data hidden, the goal is to actually get the number in excess of 100%
            data_length = len(self.EncodingData)
            data_excess = self.EncodingLength * data_length / (percentage_cutoff/100)
            print("testing encoding ", e, " percentage cutoff ", percentage_cutoff , "% ")

            for point in self.get_possible_starting_point():
                for direct in Direction:
                    data_count = 0
                    exceeded = False
                    #check one possible direction and location
                    for pointa in self.get_pixel_position(point, direct):
                        r, g, b = self.get_rgb(pointa)
                        data_added = []
                        val = [r, g, b]
                        # evaluate rgb
                        for i, s in enumerate(val):
                            if bits_changed > data_excess:
                                exceeded = True
                                break
                            if not data_count < data_length:
                                break
                            ## only starts changing data when first data bit is found
                            elif (self.check_if_data(self.EncodingData[data_count], s)):
                                data_count += 1
                                if (s & 1) == 0:  # data will need to be marked as encoded
                                    bits_changed += 1
                                else:  # data will not need to be marked as encoded
                                    pass
                            else:
                                if (s & 1 == 1):
                                    bits_changed += 1

                        if exceeded:
                            break
                        #end of for loop
                    if exceeded:
                        #print(point, direct, "exceeded bit length")
                        pass
                    else:
                        print(point, direct, "can be placed in ", bits_changed, "bits / " , data_length * self.EncodingLength, "bits percent ",  100 * (data_length * self.EncodingLength)/ bits_changed, "%  ")
                        possible.append((point,direct, self.EncodingLength,bits_changed))
                        is_found = True
                    exceeded = False
        if is_found:
            smallest_encoding = possible[0]
            for x in possible:
                if x[3] < smallest_encoding[3]:
                    smallest_encoding = x
            return smallest_encoding

        return None

    def encode_data(self, point, direction, encoding):
        data_count = 0
        bits_changed = 0
        self.set_encoding_data(encoding)
        data_length = len(self.EncodingData)
        # check one possible direction and location
        for pointa in self.get_pixel_position(point, direction):
            r, g, b = self.get_rgb(pointa)
            data_added = []
            val = [r, g, b]
            # evaluate rgb
            for i, s in enumerate(val):
                ##if done encoding data
                if not data_count < data_length:
                    break

                elif self.check_if_data(self.EncodingData[data_count], s):
                    data_count += 1
                    if (s & 1) == 0:  # data will need to be marked as encoded
                        bits_changed += 1
                    else:  # data will not need to be marked as encoded
                        pass
                else:
                    if (s & 1 == 1):
                        bits_changed += 1
        self.set_rgb(pointa, (r,g,b))
        self.save_image()

    def save_image(self):
        self.LoadedImage.save(self.OutputImageFile)
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
        if self.EncodingLength == 4:
            mask = 30
        elif self.EncodingLength == 3:
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

    # DECODE Section
    def decode(self):
        self.OriginalData = self.file_to_binary()
        self.LoadedImage = Image.open(self.InputImageFile)
        # Load the image into memory to allow pixel access.
        self.ImageWidth = self.LoadedImage.width
        self.ImageHeight = self.LoadedImage.height

        if self.LoadedImage.getbands() == 'P':
            self.Palette = self.LoadedImage.getpalette()
        else:
            self.Pixels = self.LoadedImage.load()

        points = self.find_decode_points()
        print(points)

    def check_for_full_crib(self, point, encoding):
        ##attempting all possible directions from point

        #limit is to ensure that it doesnt loop through the whole program
        pixel_limit = 10
        pixel_count = 0
        for dir in Direction:
            for x in self.get_pixel_position(point, dir):
                print()
    def find_decode_points(self, encoding):
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):

                r, g, b = self.get_rgb((x, y))
                val = (r, g, b)
                if_val = False
                for i, s in enumerate(val):
                    if self.check_if_data('1001', s) and encoding == 4:
                        if_val = True
                    elif self.check_if_data('101', s) and encoding == 3:
                        if_val = True
                    elif self.check_if_data('10', s) and encoding == 2:
                        if_val = True
                if if_val:
                    if_val = False
                    yield x,y

    def holding(self):
        img = Image.open(self.OutputImageFile)
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
    if args.verbose:
        global verbose
        verbose = True
    if args.encode:
        pat.encode()
    elif args.decode:
        pat.decode()


main()
