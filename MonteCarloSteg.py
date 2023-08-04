from PIL import Image
import argparse
from enum import Enum
import hashlib
import zlib


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
    OutputImageFile = "output.bmp"

    Input_Filename = ""

    def __init__(self):
        self.Output_File_Name = None
        self.LoadedImage = None
        self.ImageDetails = None
        self.InputData = None
        self.Data_Received = None
        self.Verbose = False
        self.Encoding_Lengths = [2, ]
        self.Threshold = 105
        self.Input_Filename = "testfile.txt"
        self.Input_Image_Filename = "test.bmp"
        self.Output_Image_Filename = "output.bmp"

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

    def set_threshold(self, threshold: str) -> None:
        self.Threshold = threshold
    def set_input_filename(self, input_image_filename: str) -> None:
        self.Input_Filename = input_image_filename
    def set_input_image_filename(self, input_image_filename: str) -> None:
        self.Input_Image_Filename = input_image_filename
    def set_output_image_filename(self, output_image_filename: str) -> None:
        self.Output_Image_Filename = output_image_filename

# Encode ####################################################################
    def encode(self):
        self.InputData = self.file_to_binary(self.Input_Filename)
        self.load_image_file(self.Input_Image_Filename)

        # Encode
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
        #attempt each encoding level
        for e in [2]:

            self.set_encoding_data(e)
            # data_excess is the factor of amount of bits that can be changed per actual data hidden, the goal is to actually get the number in excess of 100%
            data_length = len(self.Data_Ready)
            data_excess = self.EncodingLength * data_length / .5
            self.verbose("testing encoding " + str(e))
            count = 0
            #Each possible starting point will be looped by how many possible directions it can go.
            for point in self.get_possible_starting_point():
                percent_done = "{00:.3%}".format(((self.ImageWidth * point.Y) + point.X) / pixels)
                print("\r ", percent_done, "testing ", self.EncodingLength, " ", point, end="")
                count += 1
                if count % 100 == 0:
                    percent_done = "{00:.3%}".format(((self.ImageWidth * point.Y) + point.X) / pixels)
                    print("\r ", percent_done, "testing ", self.EncodingLength, " ", point, end="")
                for direct in Direction:
                    data_encoded = False
                    exceeded = False
                    data_count = 0
                    bits_changed = 0
                    # check one possible starting location and direction
                    for pointa in self.get_pixel_position(point, direct):
                        # evaluate rgb
                        for color_value in self.get_rgb(pointa):
                            if data_excess != 0 and bits_changed > data_excess: # check for if bits changed is more than allowed.
                                exceeded = True
                                break
                            elif data_count >= data_length: # check for end of data
                                last_pixel = pointa
                                data_encoded = True
                                break
                            #data we want
                            elif self.check_if_data(self.Data_Ready[data_count], color_value):
                                data_count += 1
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

                        if exceeded:
                            break
                    # end for loop color values
                    if exceeded:
                        #print(point, direct, "exceeded data length", end="")
                        pass
                    elif data_encoded:
                        data_excess = bits_changed - 1  # We only care about points that are more efficient
                        percent = "{:.6}%".format(100 * data_length * self.EncodingLength / bits_changed)
                        print("\r", self.EncodingLength, " e ", point, " -> ", last_pixel, ":\t", direct,
                              " ", bits_changed, "bits changed / ", data_length * self.EncodingLength,
                              "Hidden efficiency percent ", percent)
                        possible_encoding=(point, direct, self.EncodingLength, bits_changed)
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
        self.Hash = hashlib.md5(open(input_filename, 'rb').read()).hexdigest()
        binary_content = []
        inputfileheader = (input_filename + "::").encode()
        try:
            with open(input_filename, 'rb') as file:
                binary_data = file.read()

            binary_data = inputfileheader + binary_data
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
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):
                test = Point(x, y)
                r, g, b = self.get_rgb(test)
                val = (r, g, b)
                if_val = False
                crib = self.get_starting_crib()
                for i, s in enumerate(val):
                    if self.check_if_data(crib[0], s):
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


def parse_args():
    parser = argparse.ArgumentParser(description="Example Argument Parser")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encode", type=str, help="Specify the file to encode")
    group.add_argument("-d", "--decode", type=str, help="Specify the file to decode")
    group.add_argument("-t", "--test", type=str, help="Specify test")
    args = parser.parse_args()

    return args


def main():
    monte = MonteCarloSteg()
    args = parse_args()
    if args.verbose:
        monte.set_verbose(True)
    if args.encode:
        monte.encode()
    elif args.decode:
        monte.decode(args.decode)
    elif args.test:
        #Monte.set_File(args.test())
        monte.test()

        # Monte.test()


if __name__ == "__main__":
    main()
