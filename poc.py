from PIL import Image
import sys
import codecs
# Open the image file.


InputFile = "test.bmp"
OutputFile = "output.bmp"
DataFile = "testfile.txt"
Startcrib = "101000000101"
Endcrib = "101111111101"
def file_to_binary(file_path):
    binary_content = ""

    try:
        with open(file_path, 'rb') as file:
            while (byte := file.read(1)):
                binary_content += f'{byte[0]:08b}'
    except FileNotFoundError:
        print("The file does not exist")
        return

    return binary_content

def to_bin(data):
    return "{0:b}".format(data)

def check_if_data(value, data):
    #print(value,data)
    tempv = int(value,2)
    temp = int(data)
    temp = temp & 14
    temp = temp >> 1
    #print(temp,tempv)
    if temp == tempv:
        return True
    else:
        return False
    
def encode():

    global InputFile,OutputFile,DataFile,Startcrib,Endcrib
    img = Image.open(InputFile)
    # Load the image into memory to allow pixel access.
    pixels = img.load()
    bin = file_to_binary(DataFile)
    data = bin
    while(len(data) % 3 != 0):
        data += '0'
    data = Startcrib + bin + Endcrib
    res = [data[i:i+3] for i in range(0,len(data),3)]
    while len(res[-1])< 3:
        res[-1] += "0"

    print("data to be encoded")
    print(res)
    i = 0
    while not(i >= len(res)):
    # Go over each pixel.
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                changed = False
                stringz = "pixel {},{} ::{}.{}.{} i = {}".format(x,y,to_bin(r),to_bin(g),to_bin(b),i)
                
                #R
                if(i < len(res) and check_if_data(res[i],r)):
                    r = r | 1
                    i += 1
                    changed = True
                    if (i >= len(res)):
                        print("BREAK")
                        break

                else:
                    r = r & 254
                #G 
                if(i < len(res) and check_if_data(res[i],g)):
                    g = g | 1
                    i += 1
                    changed = True
                    if (i >= len(res)):
                        print("BREAK")
                        break

                else:
                    g = g & 254

                #B
                if(i < len(res) and check_if_data(res[i],b)):
                    b = b | 1
                    i += 1
                    changed = True
                    if (i >= len(res)):
                        print("BREAK")
                        break
                else:
                    b = b & 254
                
                if(changed):
                    print(stringz)
                    stringz = "pixel {},{} ::{}.{}.{} i = {}".format(x,y,to_bin(r),to_bin(g),to_bin(b),i)
                    print(stringz)


                # Modify the RGB values as you want, for example:
                #r = min(255, r + 50)  # Increase the red, cap at 255
                #g = max(0, g - 50)  # Decrease the green, cap at 0
                #b = max(0, b - 50)  # Decrease the blue, cap at 0

                # Update the pixel with modified values.
                pixels[x, y] = (r, g, b)

    # Save the modified image.
    img.save(OutputFile)

def decode():
    global InputFile,OutputFile,DataFile,Startcrib,Endcrib
    img = Image.open(OutputFile)
    # Load the image into memory to allow pixel access.
    pixels = img.load()

    dataout = []
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
                
            #R
            if(r & 1 == 1):
                data = (r >> 1) & 7
                #print("{}, {}".format(x,y))
                dataout.append( to_bin(data))
                    
            #G 
            if(g & 1 == 1):
                data = (g >> 1) & 7
                #print("{}, {}".format(x,y))
                dataout.append(to_bin(data))

            #B
            if(b & 1 == 1):
                data = (b >> 1) & 7
                #print("{}, {}".format(x,y))
                dataout.append(to_bin(data))
            

            if(len(dataout) == 4):
                pass
                #print("pixel {},{} ::{}.{}.{} ".format(x,y,to_bin(r),to_bin(g),to_bin(b)))
                #print(dataout)

            if(len(dataout) > 4):
                if(dataout[-1] == 5):
                    if(dataout[-2] == 7):
                        if(dataout[-3] == 7):
                            if(dataout[-4] == 5):
                                print("DATA")
                                print(dataout)
                                return
                

            
                # Modify the RGB values as you want, for example:
                #r = min(255, r + 50)  # Increase the red, cap at 255
                #g = max(0, g - 50)  # Decrease the green, cap at 0
                #b = max(0, b - 50)  # Decrease the blue, cap at 0

                # Update the pixel with modified values.
                #pixels[x, y] = (r, g, b)

    # Save the modified image.
    #img.save('output.jpg')
    print(dataout)
    print(len(dataout))
    fdat = ""
    for x in dataout[4:-4]:
        while len(x) != 3:
            x = '0'+ x
        fdat += x
    print(fdat)
    byte_data = bytes(int(fdat[i:i + 8], 2) for i in range(0, len(fdat), 8))
    with open("dataoutput.txt", "wb") as binary_file:
        binary_file.write(byte_data)
def readout():
    global InputFile, OutputFile, DataFile, Startcrib, Endcrib
    img = Image.open(OutputFile)
    # Load the image into memory to allow pixel access.
    pixels = img.load()
    for x in range(200):
        r, g, b = pixels[x, 0]
        stringz = "pixel {},{} ::{}.{}.{}".format(x,0,to_bin(r),to_bin(g),to_bin(b))
        print(stringz)


if (sys.argv[1] == "-e"):
    encode()
elif (sys.argv[1] == "-d"):
    decode()
elif (sys.argv[1] == "-r"):
    readout()
