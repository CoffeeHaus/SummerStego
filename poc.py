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
    rowbyrowsnake = 1
    columnbycolumn = 2
    columnbycolumnsnake = 3
    clockwisespiral = 4
    counterclockwisespiral = 5

class PatternSteg:
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



    def to_bin(data):
        return "{0:b}".format(data)

    def set_data_file(self):
        pass

    def set_input_image_file(self):
        pass

    def set_output_image_file(self):
        pass

    def set_data_output_file(self):
        pass
    def get_pixel_position(self, direction, starting_position):
        output = "PixelPosition: "
        output += str(direction) + " " + str(starting_position) + " " + str(self.EncodingLength)
        #starts with 0,0 which is bottom left
        if direction == Direction.rowbyrow and starting_position == Position.bottomleft:
            for y in range(self.ImageHeight):
                for x in range(self.ImageWidth):
                    yield x, y

        elif direction == Direction.columnbycolumn and starting_position == Position.bottomleft:
            for x in range(self.ImageWidth):
                for y in range(self.ImageHeight):
                    yield x, y

        #bottom left Snake
        elif direction == Direction.rowbyrowsnake and starting_position == Position.bottomleft:
            for y in range(self.ImageHeight):

                if y % 2 == 0:
                    for x in range(self.ImageWidth):
                        yield x, y
                else:
                    for x in range(self.ImageWidth-1, -1, -1):
                        yield x, y

        elif direction == Direction.columnbycolumnsnake and starting_position == Position.bottomleft:
            for x in range(self.ImageWidth):
                if x % 2 == 0:
                    for y in range(self.ImageHeight):
                        yield x, y
                else:
                    for y in range(self.ImageHeight-1, -1, -1):
                        yield x, y

        #Top Right
        elif direction == Direction.columnbycolumn and starting_position == Position.topright:
            for x in range(self.ImageWidth -1,-1,-1):
                for y in range(self.ImageHeight-1, -1, -1):
                    yield x, y

        elif direction == Direction.rowbyrow and starting_position == Position.topright:
            for y in range(self.ImageHeight-1, -1, -1):
                for x in range(self.ImageWidth-1, -1, -1):
                    yield x, y

        ##Top Right Snake
        elif direction == Direction.columnbycolumnsnake and starting_position == Position.topright:
            for x in range(self.ImageWidth -1,-1,-1):
                if x % 2 == 0:
                    for y in range(self.ImageHeight-1, -1, -1):
                        yield x, y
                else:
                    for y in range(self.ImageHeight):
                        yield x, y

        elif direction == Direction.rowbyrowsnake and starting_position == Position.topright:
            for y in range(self.ImageHeight-1, -1, -1):
                if y % 2 == 0:
                    for x in range(self.ImageWidth-1, -1, -1):
                        yield x, y
                else:
                    for x in range(self.ImageWidth):
                        yield x, y

        #Bot Right
        elif direction == Direction.columnbycolumn and starting_position == Position.bottomright:
            for x in range(self.ImageWidth-1, -1, -1):
                for y in range(self.ImageHeight):
                    yield x, y

        elif direction == Direction.rowbyrow and starting_position == Position.bottomright:
            for y in range(self.ImageHeight):
                for x in range(self.ImageWidth-1, -1, -1):
                    yield x, y

        # Bot Right snake
        elif direction == Direction.columnbycolumnsnake and starting_position == Position.bottomright:
            for x in range(self.ImageWidth-1,-1,-1):
                if x % 2 == 0:
                    for y in range(self.ImageHeight):
                        yield x, y
                else:
                    for y in range(self.ImageHeight-1,-1,-1):
                        yield x, y

        elif direction == Direction.rowbyrowsnake and starting_position == Position.bottomright:
            for y in range(self.ImageHeight):
                if y % 2 == 0:
                    for x in range(self.ImageWidth-1, -1, -1):
                        yield x, y
                else:
                    for x in range(self.ImageWidth):
                        yield x, y

        #Top left
        elif direction == Direction.columnbycolumn and starting_position == Position.topleft:
            for x in range(self.ImageWidth):
                for y in range(self.ImageHeight-1,-1,-1):
                    yield x, y

        elif direction == Direction.rowbyrow and starting_position == Position.topleft:
            for y in range(self.ImageHeight-1,-1,-1):
                for x in range(self.ImageWidth):
                    yield x, y

        # Top left snake
        elif direction == Direction.columnbycolumnsnake and starting_position == Position.topleft:
            for x in range(self.ImageWidth):
                if x % 2 == 0:
                    for y in range(self.ImageHeight-1,-1,-1):
                        yield x, y
                else:
                    for x in range(self.ImageWidth):
                        yield x, y

        elif direction == Direction.rowbyrowsnake and starting_position == Position.topleft:
            for y in range(self.ImageHeight-1,-1,-1):
                if y % 2 == 0:
                    for x in range(self.ImageWidth):
                        yield x, y
                else:
                    for x in range(self.ImageWidth - 1, -1, -1):
                        yield x, y
        # Middle ClockWise
        elif (direction == Direction.clockwisespiral or direction.counterclockwisespiral) \
                and starting_position == Position.middle:
            # Offset values for moving right, up, left, down
            if direction == Direction.clockwisespiral:
                clockwise = True
            else:
                clockwise = False
            grid_width, grid_height = int(self.ImageWidth), int(self.ImageHeight)
            dx, dy = int(self.ImageWidth/2), int(self.ImageHeight/2)
            directions = [(0, 1), (-1, 0), (0, -1), (1, 0)] if clockwise else [(0, -1), (1, 0), (0, 1), (-1, 0)]
            matrix = [[None] * grid_width for _ in range(grid_height)]

            # Yield the start position first
            yield (dx, dy)
            matrix[dy][dx] = 1

            # Continue the spiral
            for _ in range(max(grid_width, grid_height) ** 2):
                for direction in directions:
                    new_dx, new_dy = dx + direction[0], dy + direction[1]
                    if (0 <= new_dx < grid_width) and (0 <= new_dy < grid_height) and matrix[new_dy][new_dx] is None:
                        dx, dy = new_dx, new_dy
                        yield (dx, dy)
                        matrix[dy][dx] = 1
                        break
        else:
            output += " Error no path"

        print(output)




    def check_encoding(self,starting_x,starting_y):
        pass
    def Cascade_testing(self):
        pass

    def evaluate_directions(self, pixels):
        Outcomes = []
        bits_changed = 0
        possible_directions = []
        #test 3
        self.EncodingLength = 3
        data = self.OriginalData
        while len(data) % self.EncodingLength != 0:
            data += '0'
        data = self.StartCrib + data + self.EndCrib
        bytesEncoded = [data[i:i + self.EncodingLength] for i in range(0, len(data), self.EncodingLength)]
        self.EncodingData = bytesEncoded
        for dir in Direction:
            for pos in Position:
                possible_directions.append((dir, pos))

        for direct in possible_directions:
            #checking Different possible directions
            bits_changed = 0
            data_count = 0
            data_length = len(self.EncodingData)
            started = False

            for (x,y) in self.get_pixel_position(direct[0], direct[1]):
                r, g, b = pixels[x, y]
                data_added = []
                val = [r, g, b]
                # evaluate rgb
                for i, s in enumerate(val):
                    if(not data_count < data_length):
                        pass
                    ## only starts changing data when first data bit is found
                    elif(self.check_if_data(self.EncodingData[data_count], s)):
                        started = True
                        data_count += 1
                        if (s & 1) == 0:  # data will need to be marked as encoded
                            bits_changed += 1
                        else:  # data will not need to be marked as encoded
                            pass
                    elif (started):
                        if (s & 1 == 1):
                            bits_changed += 1

            Outcomes.append((bits_changed, direct, 3))

            # test 2
            self.EncodingLength = 2
            data = self.OriginalData
            while len(data) % self.EncodingLength != 0:
                data += '0'
            data = self.StartCrib + data + self.EndCrib
            bytesEncoded = [data[i:i + self.EncodingLength] for i in range(0, len(data), self.EncodingLength)]
            self.EncodingData = bytesEncoded
            # pads enough zeros to make groups of three bytes
            while len(bytesEncoded[-1]) < self.EncodingLength:
                bytesEncoded[-1] += "0"
            for direct in possible_directions:
                # checking Different possible directions
                bits_changed = 0
                data_count = 0
                data_length = len(self.EncodingData)
                started = False

                for (x, y) in self.get_pixel_position(direct[0], direct[1]):
                    r, g, b = pixels[x, y]
                    data_added = []
                    val = [r, g, b]
                    # evaluate rgb
                    for i, s in enumerate(val):
                        if (not data_count < data_length):
                            pass
                        ## only starts changing data when first data bit is found
                        elif (self.check_if_data(self.EncodingData[data_count], s)):
                            started = True
                            data_count += 1
                            if (s & 1) == 0:  # data will need to be marked as encoded
                                bits_changed += 1
                            else:  # data will not need to be marked as encoded
                                pass
                        elif (started):
                            if (s & 1 == 1):
                                bits_changed += 1

                Outcomes.append((bits_changed, direct, 2))
            #end of for loop
        print(Outcomes)


    def check_encoding(self):
        pass

    def encode(self):
        img = Image.open(self.InputImageFile)
        # Load the image into memory to allow pixel access.
        pixels = img.load()
        self.OriginalData = self.file_to_binary()

        self.ImageWidth = img.width
        self.ImageHeight = img.height

        #print("data to be encoded")
        #print(bytesEncoded)
        #self.EncodingData = bytesEncoded

        self.evaluate_directions(pixels)



    def encode_data(self, x, y):

        data_count = 0
        bits_changed = 0
        lastx = 0
        lasty = 0
        test = img.getbands()
        if 'P' in test:
            palette = img.getpalette()
            self.ImageHeight = img.height
            self.ImageWidth = img.width

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
        img.save(self.OutputImageFile)
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
