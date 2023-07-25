from PIL import Image
import sys
import argparse
from enum import Enum
import hashlib
import zlib
import bitstring
import threading

verbose = True


def verbose(string):
    global verbose
    if verbose:
        print(string)


class Direction(Enum):
    row = 0
    rowreverse = 2
    column = 3
    columnreverse = 5


class MonteCarloSteg:
    starting_crib = {5: ['10101', '01010', '10101', '01010', '10101'],
                     4: ['1001', '0101', '0101', '0101', '0101', '1001'],
                     3: ['101', '010', '101', '010', '101', '010', '101'],
                     2: ['10', '01', '01', '10', '01', '10', '01', '10', '01', '10', '01']}

    ending_crib = {5: ['10101', '10101', '01010', '10101', '10101'],
                   4: ['1001', '1010', '1010', '1010', '1010', '1001'],
                   3: ['101', '101', '010', '101', '010', '010', '101'],
                   2: ['10', '01', '10', '01', '10', '01', '10', '01', '10', '10', '01']}

    Encoding_Lengths = [5, 4, 3, 2]
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

    def __init__(self):
        self.InputData = None

    def file_to_binary(self, InputFilename):
        self.Hash = hashlib.md5(open(InputFilename, 'rb').read()).hexdigest()
        binary_content = []
        inputfileheader = (InputFilename + "::").encode()
        try:
            with open(InputFilename, 'rb') as file:
                binary_data = file.read()

            binary_data = inputfileheader + binary_data
            #compressed_data = binary_data
            compressed_data = zlib.compress(binary_data)
            compressed_data += ("::" + self.Hash).encode()
        except FileNotFoundError:
            print("The input file does not exist")
            return
        bitstring.BitArray()
        data_in_ints = [format(int(byte), 'd') for byte in compressed_data]
        self.Starting_Hex_Values = [hex(int(x)) for x in data_in_ints]
        binary_string = ''.join(format(byte, '08b') for byte in compressed_data)
        return binary_string

    def get_pixel_position(self, starting_point, direction):
        starting_x, starting_y = starting_point
        # starts at point which is bottom left
        if direction == Direction.row:
            for y in range(starting_y, self.ImageHeight):
                for x in range(starting_x, self.ImageWidth):
                    yield x, y
                starting_x = 0

        elif direction == Direction.column:
            for x in range(starting_x, self.ImageWidth):
                for y in range(starting_y, self.ImageHeight):
                    yield x, y
                starting_y = 0

        # starts at point which is bottom left
        if direction == Direction.rowreverse:
            for y in range(starting_y, self.ImageHeight):
                for x in range(starting_x, -1, -1):
                    yield x, y
                starting_x = self.ImageWidth - 1

        elif direction == Direction.columnreverse:
            for x in range(starting_x, self.ImageWidth):
                for y in range(starting_y, -1, -1):
                    yield x, y
                starting_y = self.ImageHeight - 1

    def Load_Image_File(self, input_image_file):

        self.ImageDetails = Image.open(input_image_file)
        verbose("Image info" + str(vars(self.ImageDetails)))
        self.LoadedImage = self.ImageDetails.load()
        self.ImageWidth = self.ImageDetails.width
        self.ImageHeight = self.ImageDetails.height

    def Save_Binary_File(self):
        with open(self.Output_File_Name, 'wb') as file:
            file.write(self.Data_Recieved)


    def test(self, input_filename="testfile.txt", input_image_filename="test.bmp", output_image_filename="output.bmp"):
        print("TEST started")
        self.InputData = self.file_to_binary(input_filename)
        self.Load_Image_File(input_image_filename)

        # Encode
        print("Encode started x-",self.ImageWidth,"  y-",self.ImageHeight)
        best_case = self.test_encode()
        if best_case:
            point, direction, encoding, bits = best_case
            self.encode_data(point, direction, encoding)

        self.save_image()

        # Decode
        print("Decoding started")
        self.Load_Image_File(output_image_filename)

        for enco in (2, 3, 4):
            points = []
            self.EncodingLength = enco
            for p in self.find_decode_points(enco):
                full_crib = []
                for dir in Direction:
                    if self.check_for_full_crib(p, dir):
                        points.append((p, dir))
            out = "Points found for decoding " + str(enco) + " :" + str(points)
            verbose(out)
            for p in points:
                decoded = self.attempt_decode_at_point(p[0], p[1])
                if(decoded):
                    if(self.data_decode(decoded)):
                        self.Output_File_Name = b"output_" + self.Output_File_Name
                        self.Save_Binary_File()
                        return
                print(decoded)
        print(points)

        self.Save_Binary_File()

    def data_decode(self, data):
        temp = data
        temp = data[len(self.get_starting_crib()):len(data)-len(self.get_ending_crib())]
        onezeros = ''.join(temp)
        byte_values = [int(onezeros[i:i+8], 2) for i in range(0, len(onezeros), 8)]
        byte_string= bytes(byte_values)
        data= byte_string.split(b"::")

        uncompressed_data = zlib.decompress(data[0])
        filename, data = uncompressed_data.split(b"::")
        self.Data_Recieved = data
        self.Output_File_Name = filename
        return True



    def save_image(self):
        print(type(self.LoadedImage))
        self.ImageDetails.save(self.OutputImageFile)
        # self.LoadedImage.save(self.OutputImageFile)

    def encode_data(self, point, direction, encoding):
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
        if not length in self.Encoding_Lengths:
            print("ERROR incorrect encoding length")

        self.EncodingLength = length
        data = self.InputData
        while len(data) % self.EncodingLength != 0:  # pads data to fit into encoding length groups
            data += '0'
        segmented_data = [data[i:i + self.EncodingLength] for i in range(0, len(data), self.EncodingLength)]
        self.Data_Ready = list(self.get_starting_crib()) + segmented_data + list(self.get_ending_crib())  # adds start crib and end crib

    def encode(self, input_filename="testfile.txt", input_image_filename="test.bmp",
               output_image_filename="output.bmp"):
        self.InputData = self.file_to_binary(input_filename)
        self.Load_Image_File(input_image_filename)

    def test_encode(self):
        possible_encoding = None
        last_pixel = None
        pixels = self.ImageHeight * self.ImageWidth
        for e in [2,3,4]:

            self.set_encoding_data(e)
            # data_excess is the factor of amount of bits that can be changed per actual data hidden, the goal is to actually get the number in excess of 100%
            data_length = len(self.Data_Ready)
            data_excess = 0#self.EncodingLength * data_length / (percentage_cutoff / 100)
            verbose("testing encoding " + str(e))
            lis = [x for x in self.get_possible_starting_point()]
            count = 0
            tot = len(lis)
            #Each possible starting point will be looped by how many possible directions it can go.
            for point in self.get_possible_starting_point():
                for direct in Direction:
                    count += 1
                    percent_done = "{00:.3%}".format(count/tot)
                    print("\r ",percent_done,"testing ",self.EncodingLength," ", point, ":", direct, end="")
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
                        data_excess = bits_changed -1
                        print(self.EncodingLength, " :: ", point, " -> ", last_pixel, ": ", direct, " can be placed in "\
                              , bits_changed, "bits / ", data_length * self.EncodingLength, "bits percent ",
                              100 * (data_length * self.EncodingLength) / bits_changed, "%  ")
                        possible_encoding=(point, direct, self.EncodingLength, bits_changed)
                        if 100 * (data_length * self.EncodingLength) / bits_changed > 90:
                            return possible_encoding
                    else: # ran out of pixels
                        pass
                    exceeded = False

                # end of direction for loop
            #end of starting point for loop
        # If

        return possible_encoding


    def decode(self):
        self.OriginalData = self.file_to_binary()
        self.LoadedImage = Image.open(self.OutputImageFile)
        # Load the image into memory to allow pixel access.
        self.ImageWidth = self.LoadedImage.width
        self.ImageHeight = self.LoadedImage.height

        if self.LoadedImage.getbands() == 'P':
            self.Palette = self.LoadedImage.getpalette()
        else:
            self.Pixels = self.LoadedImage.load()
        for enco in (4, 3, 2):
            points = []
            self.EncodingLength = enco
            for p in self.find_decode_points(enco):
                full_crib = []
                for dir in Direction:
                    if self.check_for_full_crib(p, dir):
                        points.append((p, dir))
            out = "Points found for decoding " + str(enco) + " :" + str(points)
            verbose(out)
            for p in points:
                self.attempt_decode_at_point(p[0], p[1])
        print(points)

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

    def find_decode_points(self, encoding):
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):

                r, g, b = self.get_rgb((x, y))
                val = (r, g, b)
                if_val = False
                for i, s in enumerate(val):
                    if self.check_if_data(self.get_starting_crib()[0], s):
                        if_val = True
                if if_val:
                    if_val = False
                    yield x, y

    def Read_Data(self, value):
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

        for xy in self.get_pixel_position(point, direction):
            x, y = xy
            r, g, b = self.get_rgb((x, y))
            val = (r, g, b)

            for i, s in enumerate(val):

                if not started:  # this is to skip until we find the starting crib in the pixel, which could be in the second or third RGB value
                    if self.check_if_data(crib[0], s):
                        started = True
                        data_count += 1
                        out_data.append(self.Read_Data(s))

                elif (s & 1) == 1:  # found value
                    data_count += 1
                    out_data.append(self.Read_Data(s))
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

    def get_starting_crib(self):
        return self.starting_crib[self.EncodingLength]

    def get_ending_crib(self):
        return self.ending_crib[self.EncodingLength]

    def check_for_full_crib(self, point, direction):
        ##attempting all possible directions from point

        # limit is to ensure that it doesnt loop through the whole program
        pixel_limit = 20
        pixel_count = 0
        data_count = 0
        data_length = len(self.get_starting_crib())

        started = False

        for xy in self.get_pixel_position(point, direction):
            new_data_added = False
            x, y = xy
            r, g, b = self.get_rgb((x, y))
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

    def get_possible_starting_point(self):
        for y in range(self.ImageHeight):
            for x in range(self.ImageWidth):

                r, g, b = self.get_rgb((x, y))
                val = (r, g, b)
                if_val = False
                crib = self.get_starting_crib()
                for i, s in enumerate(val):
                    if self.check_if_data(crib[0], s):
                        if_val = True
                if if_val:
                    if_val = False
                    yield x, y

    def set_rgb(self, point, rgb):

        if self.If_Palette:
            index = self.LoadedImage.getpixel(point)  # index in the palette
            base = 3 * index  # because each palette color has 3 components
            self.Palette[base] = rgb[0]
            self.Palette[base + 1] = rgb[1]
            self.Palette[base + 2] = rgb[2]
        else:
            self.LoadedImage[point] = rgb
            # self.LoadedImage.putpixel(point, rgb)

    def get_rgb(self, point):

        if self.Palette:
            index = self.LoadedImage.getpixel(point)  # index in the palette
            base = 3 * index  # because each palette color has 3 components
            return self.Palette[base:base + 3]
        else:
            return self.LoadedImage[point]


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
    Monte = MonteCarloSteg()
    args = parse_args()
    if args.verbose:
        global verbose
        verbose = True
    if args.encode:
        Monte.encode()
        # Monte.set_File()
    elif args.decode:
        Monte.decode()
    elif args.test:
        # Monte.set_File(args.encode())
        Monte.test()

        # Monte.test()


if __name__ == "__main__":
    main()
