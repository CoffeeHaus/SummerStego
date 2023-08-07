##
# Team 4 - Monte Carlo Stego
# Andrew Neumann
# Madeline Kotara
# Haven Kotara
# Please ensure you have PIL installed. https://pillow.readthedocs.io/en/stable/
# Please ensure you have filetype installed. https://pypi.org/project/filetype/
# To install the above packages you need pip https://pypi.org/project/pip/
# This program was developed with python 3.7+ in mind
# How to use this program:
# Hide some data: python3 MonteCarloSteg.py encode -i <path to cover image> -m <path to message> -o <file to write the stego image to>
# Extract some data: python3 MonteCarloSteg.py decode -x <path to stego image>
##

#!/usr/bin/python3
from PIL import Image
import argparse
from enum import Enum
import hashlib
import zlib
import sys
import filetype
import numpy as np


class Direction(Enum):
    row = 0
    rowreverse = 2
    column = 3
    columnreverse = 5


class Point:
    def __init__(self, x: int, y: int):
        self.X = x
        self.Y = y

    def to_tuple(self):
        return (self.X, self.Y)

    def __str__(self):
        return "({}, {})".format(self.X, self.Y)


class MonteCarloSteg:
    starting_crib = {5: ['10101', '01010', '10101', '01010', '10101'],
                     4: ['1001', '0101', '0101', '0101', '0101', '1001'],
                     3: ['101', '010', '101', '010', '101', '010', '101'],
                     2: ['10', '01', '01', '10', '01', '10', '01', '10', '01', '10', '01']}

    ending_crib = {5: ['10101', '10101', '01010', '10101', '10101'],
                   4: ['1001', '1010', '1010', '1010', '1010', '1001'],
                   3: ['101', '101', '010', '101', '010', '010', '101'],
                   2: ['10', '01', '10', '01', '10', '01', '10', '01', '10', '10', '01']}

    If_Palette = False
    ImageHeight = 0
    ImageWidth = 0
    Palette = None
    Pixels = None
    InputData = None
    Data_Ready = None
    EncodingLength = 0
    Hash = ""
    OutputImageFile = ""

    Input_Filename = ""

    def __init__(self):
        self.Output_File_Name = None
        self.LoadedImage = None
        self.ImageDetails = None
        self.InputData = None
        self.Data_Received = None
        self.Verbose = False
        self.Encoding_Lengths = [2, ]
        self.Threshold = 92
        self.Input_Filename = ""
        self.Input_Image_Filename = ""
        self.Output_Image_Filename = ""

    # Utils

    def verbose(self, string: str) -> None:
        if self.Verbose:
            print(string)

    def set_verbose(self, value: bool) -> None:
        self.Verbose = value

    def get_starting_crib(self) -> list:
        return self.starting_crib[self.EncodingLength]

    def get_ending_crib(self):
        return self.ending_crib[self.EncodingLength]

    def check_if_data(self, data_value, color_value):
        # verbose(value,data)
        # data
        bits = self.EncodingLength + 1
        mask = (int(255 >> bits) << bits) ^ 255  # mask to remove non essential bits
        temp = int(color_value) & mask
        temp = temp >> 1
        # value
        value_in_bin = int(data_value, 2)
        if temp == value_in_bin:
            return True
        else:
            return False

    def get_pixel_position(self, starting_point: Point, direction) -> Point:
        starting_x = starting_point.X
        starting_y = starting_point.Y
        # starts at point which is bottom left
        if direction == Direction.row:
            for y in range(starting_y, self.ImageHeight):
                for x in range(starting_x, self.ImageWidth):
                    yield Point(x, y)
                starting_x = 0

        elif direction == Direction.column:
            for x in range(starting_x, self.ImageWidth):
                for y in range(starting_y, self.ImageHeight):
                    yield Point(x, y)
                starting_y = 0

        # starts at point which is bottom left
        if direction == Direction.rowreverse:
            for y in range(starting_y, self.ImageHeight):
                for x in range(starting_x, -1, -1):
                    yield Point(x, y)
                starting_x = self.ImageWidth - 1

        elif direction == Direction.columnreverse:
            for x in range(starting_x, self.ImageWidth):
                for y in range(starting_y, -1, -1):
                    yield Point(x, y)
                starting_y = self.ImageHeight - 1

    def save_image(self, output_file: str):
        self.ImageDetails.save(output_file)

    def encode_data(self, point: Point, direction: Direction, encoding: int):
        data_count = 0
        bits_changed = 0
        last_point = None
        self.set_encoding_data(encoding)
        data_length = len(self.Data_Ready)
        # check one possible direction and location
        for pointa in self.get_pixel_position(point, direction):
            r, g, b = self.get_rgb(pointa)
            data_added = []
            val = [r, g, b]
            last_point = pointa
            # Loops through r, g, b
            for i, s in enumerate(val):

                ##if done encoding data
                if not data_count < data_length:

                    break

                elif self.check_if_data(self.Data_Ready[data_count], s):
                    data_count += 1
                    if (s & 1) == 0:  # data will need to be marked as encoded
                        val[i] = s + 1
                        bits_changed += 1

                    else:  # data will not need to be marked as encoded
                        pass

                else:
                    if (s & 1 == 1):
                        val[i] = s - 1
                        bits_changed += 1
            self.set_rgb(pointa, tuple(val))
        print(point, " -> ", last_point)

    def set_encoding_data(self, length):
        if length not in self.Encoding_Lengths:
            print("ERROR incorrect encoding length")

        self.EncodingLength = length
        data = self.InputData
        while len(data) % self.EncodingLength != 0:  # pads data to fit into encoding length groups
            data += '0'
        segmented_data = [data[i:i + self.EncodingLength] for i in range(0, len(data), self.EncodingLength)]
        self.Data_Ready = list(self.get_starting_crib()) + segmented_data + list(self.get_ending_crib())  # adds start crib and end crib

    def get_rgb(self, point: Point):

        if self.Palette:
            index = self.LoadedImage.getpixel(point.to_tuple())  # index in the palette
            base = 3 * index  # because each palette color has 3 components
            return self.Palette[base:base + 3]
        else:
            return self.LoadedImage[point.to_tuple()]

    def set_threshold(self, threshold: int) -> None:
        self.Threshold = threshold

    def set_input_filename(self, input_image_filename: str) -> None:
        self.Input_Filename = input_image_filename

    def set_input_image_filename(self, input_image_filename: str) -> None:
        self.Input_Image_Filename = input_image_filename

    def set_output_image_filename(self, output_image_filename: str) -> None:
        self.Output_Image_Filename = output_image_filename

    def get_input_image_filename(self):
        return self.Input_Image_Filename

# Encode ####################################################################
    def encode(self):
        self.InputData = self.file_to_binary(self.Input_Filename)
        self.load_image_file(self.Input_Image_Filename)

        # Encode
        print("WARNING: This may be *very* slow depending on how big the input image is")
        print("Encode started x-", self.ImageWidth, "  y-", self.ImageHeight)
        best_case = self.test_encode()
        if best_case:
            point, direction, encoding, bits = best_case
            self.encode_data(point, direction, encoding)

        self.save_image(self.Output_Image_Filename)

    def test_encode(self) -> tuple:
        possible_encoding = None
        last_pixel = None
        pixels = self.ImageHeight * self.ImageWidth

        dtype = np.dtype([('r', int), ('g', int), ('b', int)])


        array = np.empty((self.ImageWidth, self.ImageHeight), dtype=dtype)
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):
                r, g, b = self.get_rgb(Point(x, y))
                a = array[x][y]
                array[x][y] = ((r>>1)&3, (g>>1)&3, (b>>1)&3)

        #attempt each encoding level
        for e in [2]:

            self.set_encoding_data(e)
            mask = 3

            data_bits = [int(x, 2) for x in self.Data_Ready]

            # data_excess is the factor of amount of bits that can be changed per actual data hidden, the goal is to actually get the number in excess of 100%
            data_length = len(self.Data_Ready)
            data_excess = self.EncodingLength * data_length / .1
            self.verbose("testing encoding " + str(e))
            count = 0
            #Each possible starting point will be looped by how many possible directions it can go.
            for point in self.get_possible_starting_point():
                count -= 1
                if count <= 0:
                    count = 8
                    percent_done = "{00:.3%}".format(((self.ImageWidth * point.Y) + point.X) / pixels)
                    print(f"\r {percent_done} testing {self.EncodingLength} {point}", end="")

                for direct in Direction:
                    data_encoded = False
                    exceeded = False
                    data_count = 0
                    bits_changed = 0
                    bln_5_percent = False
                    int_5_percent = int(data_length/20)
                    int_5_percent_excess = int(data_excess/20)
                    # check one possible starting location and direction
                    for pointa in self.get_pixel_position(point, direct):
                        if data_excess != 0 and bits_changed > data_excess:  # check for if bits changed is more than allowed.
                            exceeded = True
                            break
                        elif bln_5_percent: # check at the 5 percent point to see if data is being effiecnt
                            if bits_changed > int_5_percent_excess:
                                exceeded = True
                                break
                            else:
                                bln_5_percent = False

                        # evaluate rgb
                        for color_value in array[pointa.X][pointa.Y]:
                            if data_count == data_length:  # check for end of data
                                last_pixel = pointa
                                data_encoded = True
                                break
                            data = data_bits[data_count] ## troubleshooting
                            if color_value == data_bits[data_count]:
                                data_count += 1
                                if int_5_percent == data_count:
                                    bln_5_percent = True
                                if (color_value & 1) == 0:  # data will need to be marked as encoded
                                    bits_changed += 1
                                else:  # data will not need to be marked as encoded, because it already is
                                    pass
                            #doesnt contain data we want
                            else:
                                if color_value & 1 == 1:
                                    bits_changed += 1
                                else: # the data is not what is needed and doesnt need to be encoded.
                                    pass
                        if data_encoded:
                            break
                        if exceeded:
                            break
                    # end for loop color values
                    if exceeded:
                        #print(point, direct, "exceeded data length", end="")
                        pass
                    elif data_encoded:
                        data_excess = int(bits_changed * .98)  # We only care about points that are more efficient
                        percent = "{:.6}%".format(100 * data_length * self.EncodingLength / bits_changed)
                        print(f"\r{self.EncodingLength} e {point} -> {last_pixel}:\t {direct} ({bits_changed} /{data_length * self.EncodingLength}) bits changed / bits hidden = {percent} efficiency")
                        possible_encoding = (point, direct, self.EncodingLength, bits_changed)
                        if 100 * (data_length * self.EncodingLength) / bits_changed > self.Threshold:
                            return possible_encoding
                    else: # ran out of pixels
                        pass
                    exceeded = False

                # end of direction for loop
            #end of starting point for loop
        # If

        return possible_encoding

    def file_to_binary(self, input_filename: str) -> str:

        binary_content = []
        inputfileheader = (input_filename + "::").encode()
        try:
            with open(input_filename, 'rb') as file:
                binary_data = file.read()

            binary_data = inputfileheader + binary_data
            self.Hash = hashlib.md5(binary_data).hexdigest()
            #compressed_data = binary_data
            compressed_data = zlib.compress(binary_data)
            compressed_data += ("::" + self.Hash).encode()
        except FileNotFoundError:
            print("The input file does not exist")
            return
        data_in_ints = [format(int(byte), 'd') for byte in compressed_data]
        self.Starting_Hex_Values = [hex(int(x)) for x in data_in_ints]
        binary_string = ''.join(format(byte, '08b') for byte in compressed_data)
        return binary_string

    def load_image_file(self, input_image_file: str) -> None:

        self.ImageDetails = Image.open(input_image_file)
        self.verbose("Image info" + str(vars(self.ImageDetails)))
        self.LoadedImage = self.ImageDetails.load()
        self.ImageWidth = self.ImageDetails.width
        self.ImageHeight = self.ImageDetails.height

    def get_possible_starting_point(self) -> Point:
        crib = int(self.get_starting_crib()[0], 2)

        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):
                test = Point(x, y)
                r, g, b = self.get_rgb(test)
                rgb = (r, g, b)
                if_val = False
                for v in rgb:
                    if (v >> 1) & 3 == crib:
                        if_val = True

                if if_val:
                    if_val = False
                    yield test

    def set_rgb(self, point: Point, rgb: tuple) -> None:

        if self.If_Palette:
            index = self.LoadedImage.getpixel(point.to_tuple())  # index in the palette
            base = 3 * index  # because each palette color has 3 components
            self.Palette[base] = rgb[0]
            self.Palette[base + 1] = rgb[1]
            self.Palette[base + 2] = rgb[2]
        else:
            self.LoadedImage[point.to_tuple()] = rgb

# Decode ####################################################################
    def decode(self):
        self.load_image_file(self.Output_Image_Filename)

        for enco in [2,]:
            points = []
            self.EncodingLength = enco
            for p in self.find_decode_points(enco):
                full_crib = []
                for dir in Direction:
                    if self.check_for_full_crib(p, dir):
                        points.append((p, dir))
            out = "Points found for decoding " + str(enco) + " :" + str(points)
            self.verbose(out)
            for point, direct in points:
                decoded = self.attempt_decode_at_point(point, direct)
                if(decoded):
                    if(self.data_decode(decoded)):
                        self.Output_File_Name = self.Output_File_Name + b".output"
                        self.save_binary_file()
                        return

        self.save_binary_file()

    def data_decode(self, data):
        temp = data
        one_zeros = ''.join(data[len(self.get_starting_crib()):len(data)-len(self.get_ending_crib())])
        byte_values = [int(one_zeros[i:i+8], 2) for i in range(0, len(one_zeros), 8)]
        byte_string= bytes(byte_values)
        data= byte_string.split(b"::")

        uncompressed_data = zlib.decompress(data[0])
        filename, data = uncompressed_data.split(b"::")
        self.Data_Received = data
        self.Output_File_Name = filename
        return True

    def find_decode_points(self, encoding: int) -> Point:
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):
                test = Point(x, y)
                r, g, b = self.get_rgb(test)
                val = (r, g, b)
                if_val = False
                for i, s in enumerate(val):
                    if self.check_if_data(self.get_starting_crib()[0], s):
                        if_val = True
                if if_val:
                    if_val = False
                    yield test

    def read_data(self, value: int):
        # verbose(value,data)
        # data
        bits = 8 - self.EncodingLength
        mask = int(255 >> bits)  # mask to remove non essential bits
        temp = int(value) >> 1
        temp = temp & mask
        # value "{:07.3f}".format(varInt)
        fstring = "{:0" + str(self.EncodingLength) + "b}"
        ret_value = fstring.format(temp)
        return ret_value

    def attempt_decode_at_point(self, point, direction):
        ##attempting all possible directions from point
        crib = self.get_starting_crib()
        out_data = []
        data_count = 0
        data_length = len(crib)

        started = False

        for p in self.get_pixel_position(point, direction):
            r, g, b = self.get_rgb(p)
            val = (r, g, b)

            for i, s in enumerate(val):

                if not started:  # this is to skip until we find the starting crib in the pixel, which could be in the second or third RGB value
                    if self.check_if_data(crib[0], s):
                        started = True
                        data_count += 1
                        out_data.append(self.read_data(s))

                elif (s & 1) == 1:  # found value
                    data_count += 1
                    out_data.append(self.read_data(s))
                    a = data_count > len(self.get_ending_crib()) * 2
                    b = self.get_ending_crib()[-1]
                    c = out_data[-1]
                    d = b == c
                    if data_count > len(self.get_ending_crib()) * 2 \
                            and self.get_ending_crib()[-1] == out_data[-1]:  # check if end crib is found

                        l = len(self.get_ending_crib())
                        match = True
                        for ec in range(len(self.get_ending_crib())):
                            data = out_data[-(ec + 1)]
                            cri = self.get_ending_crib()[-(ec + 1)]
                            if out_data[-(ec + 1)] != self.get_ending_crib()[-(ec + 1)]:
                                match = False
                                break
                        if match:
                            return out_data
                    bln_new_data = False
                elif (s & 0) == 1:  # if there is a value that does not match the starting crib, then return false
                    pass

    def check_for_full_crib(self, point: Point, direction: Direction):
        ##attempting all possible directions from point

        # limit is to ensure that it doesnt loop through the whole program
        pixel_limit = 20
        pixel_count = 0
        data_count = 0
        data_length = len(self.get_starting_crib())

        started = False

        for p in self.get_pixel_position(point, direction):
            new_data_added = False
            r, g, b = self.get_rgb(p)
            val = (r, g, b)
            if pixel_count > pixel_limit:  # set limit on how long the loop goes before giving up on looking for the crib
                return False
            elif data_count == data_length:  # if we have found the all the data in the correct order return True
                return True
            for i, s in enumerate(val):
                if data_count == data_length:  # if we have found the all the data in the correct order return True
                    return True

                if not started:  # this is to skip until we find the starting crib in the pixel, which could be in the second or third RGB value
                    if self.check_if_data(self.get_starting_crib()[data_count], s):
                        started = True
                        data_count += 1
                        new_data_added = True
                elif (s & 1) == 1 and self.check_if_data(self.get_starting_crib()[data_count],
                                                         s):  # found value and it matched expected crib
                    data_count += 1
                elif (s & 1) == 1:  # if there is a value that does not match the starting crib, then return false
                    return False

            pixel_count += 1

    def save_binary_file(self) -> None:
        with open(self.Output_File_Name, 'wb') as file:
            file.write(self.Data_Received)

    # Test ####################################################################
    def test(self):
        print("TEST started")
        self.encode()

        # Decode
        print("Decoding started")
        self.decode()
# end of class MonteCarloSteg

#TODO
#Fix this to not accept -o with -e
def parse_args():

    parent_parser = argparse.ArgumentParser(description="The Monte Carlo Steganography Utility is used to encode or decode a file. Right now\
                                     the tool has limited functionality/support but does work in practice. More features\
                                     and testing are needed and may be implemented if time permits.", epilog="Specify \"encode -h\" or \"decode -h\" to see usage information for each operation. \
                                        Only BMP files are supported for the cover image.")
    

    subparsers = parent_parser.add_subparsers(help="Choose an operating mode", dest='mode')

    encode_parser = subparsers.add_parser('encode', help='encode a cover image with a message file to produce a stego image')
    encode_parser.add_argument("-i", "--input", type=str, required=False, default="cover.bmp", help="Specify the name/path of the cover file")
    encode_parser.add_argument("-m", "--message", type=str, required=True, help="Specify the name/path of the message file to embed")
    encode_parser.add_argument("-o", "--output", type=str, required=False, default="output.bmp", help="Specify the name/path of the stego image being created")
    encode_parser.add_argument("-t", "--threshold", type=int, required=False, help="percent threshold")
    encode_parser.set_defaults(action=lambda: 'encode')

    decode_parser = subparsers.add_parser('decode', help='decode a stego image to retrieve the hidden message')
    decode_parser.add_argument("-x", "--extract", type=str, required=True, help="Specify the name/path of the stego image to extract the message from")
    decode_parser.set_defaults(action=lambda: 'decode')

    args = parent_parser.parse_args()

    return args


def main():
    monte = MonteCarloSteg()
    args = parse_args()
    #if args.verbose:
    ##    monte.set_verbose(True)
    if args.mode == 'encode':
        if args.threshold:
            monte.set_threshold(args.threshold)
        monte.set_input_image_filename(args.input)
        monte.set_input_filename(args.message)
        monte.set_output_image_filename(args.output)
        kind = filetype.guess(args.input)
        if kind.mime != "image/bmp":
            print("Cover image must be a BMP")
            sys.exit(-1)
        monte.encode()
    elif args.mode == 'decode':
        monte.set_output_image_filename(args.extract)
        monte.decode()
    #elif args.test:
    #    monte.test()
    else:
        print("Invalid arguments specificed, please rerun with -h flag")
        sys.exit(-1)


if __name__ == "__main__":
    main()
