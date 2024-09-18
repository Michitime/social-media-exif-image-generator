from sys import argv
import os
from fractions import Fraction
from PIL import Image, ImageFont, ImageDraw, ExifTags, ImageFilter

#########################################
# FUNCTIONS
#########################################


#######################################################
# convert shutter speed float to fraction
def getShutterSpeedFormat(shutterSpeed):
    if shutterSpeed < 1:
        shutterSpeed = Fraction(shutterSpeed).limit_denominator()
        return shutterSpeed
    elif shutterSpeed > 1:
        shutterSpeed = round(shutterSpeed)
        return shutterSpeed


#######################################################
# calculate brightness of image (0 = black, 1 = white)
def calculate_brightness(image):
    greyscale_image = image.convert("L")
    histogram = greyscale_image.histogram()
    pixels = sum(histogram)
    brightness = scale = len(histogram)

    for index in range(0, scale):
        ratio = histogram[index] / pixels
        brightness += ratio * (-scale + index)

    return 1 if brightness == 255 else brightness / scale


#######################################################
# calculate text size based on image size
def calulateTextSize(image_size):
    width = image_size[0]
    height = image_size[1]
    size = width / 10 if width > height else height / 10

    # if image is landscape, make text smaller
    if image_size[0] > image_size[1]:
        size = size * 0.9
    return size


#######################################################
# calculate text position based on image size and text size
def calulateTextPosition(image_size, width, heigth):
    image_width = image_size[0]
    image_height = image_size[1]
    x = (image_width - width) / 2
    y = (image_height - heigth) / 2
    return x, y


#######################################################
# check if text and background should be white or black
def getColorForTextandBackground(image):
    brightness = calculate_brightness(image)
    if brightness < 0.5:
        return (0, 0, 0, 254), (255, 255, 255, 90)
    else:
        return (255, 255, 255, 254), (0, 0, 0, 90)


######################################
# open image and get exif data
def getImageData(image_name):
    image = Image.open(image_name)
    image.verify()

    exif_data = image.getexif()
    image_size = image.size
    cameratype = exif_data.get(272)
    exdented_exif_data = exif_data.get_ifd(ExifTags.IFD.Exif)
    lensModel = exdented_exif_data[ExifTags.Base.LensModel]
    focalLength = exdented_exif_data[ExifTags.Base.FocalLengthIn35mmFilm]
    fStop = str(exdented_exif_data[ExifTags.Base.FNumber])
    # remove .0 from fStop  if it is a whole number
    if fStop.endswith(".0"):
        fStop = fStop[:-2]
    shutterSpeed = getShutterSpeedFormat(exdented_exif_data[ExifTags.Base.ExposureTime])
    ISO_number = exdented_exif_data[ExifTags.Base.ISOSpeedRatings]

    # create string to be used on image for exif info
    exif_info_string = (
        str(cameratype)
        + "\n"
        + str(focalLength)
        + "mm"
        + "\n"
        + "f/"
        + str(fStop)
        + "\n"
        + "ISO "
        + str(ISO_number)
        + "\n"
        + str(shutterSpeed)
        + " sec"
    )

    # create string to be used on image for capture data
    capture_data_string = (
        str(focalLength)
        + "mm"
        + "\n"
        + "f/"
        + str(fStop)
        + "\n"
        + "ISO "
        + str(ISO_number)
        + "\n"
        + str(shutterSpeed)
        + " sec"
    )

    # create string to be used on image for equipment
    equiment_string = (
        str(cameratype)
        if ("iPhone" in cameratype)
        else str(cameratype) + "\n" + str(lensModel)
    )

    image.close()
    return (
        cameratype,
        lensModel,
        focalLength,
        fStop,
        shutterSpeed,
        ISO_number,
        exif_info_string,
        capture_data_string,
        equiment_string,
        image_size,
    )


###################################
# get font type based on cameratype
def getFontType(cameratype):

    if "iPhone" in cameratype:
        font_type = "OpenRunde-Semibold.otf"
    else:
        font_type = "OpenRunde-Semibold.otf"

    return font_type


############################
# get font setup image size
def getFontSetup(image_size):
    font_type = "OpenRunde-Semibold.otf"
    font_size = calulateTextSize(image_size)
    # setup parameters for text
    font_settings = ImageFont.truetype(font_type, size=font_size)
    font_equipment = ImageFont.truetype(font_type, size=font_size * 0.7)

    return font_settings, font_equipment, font_type, font_size


##########################################################
# calculate textbox size based on image size and font size
def calculateTextboxSize(image_data):
    # create empty image to calculate text size
    empty_image = Image.new("RGBA", image_data[9])
    draw = ImageDraw.Draw(empty_image)

    # get font setup data
    font_setup_capture_data, font_setup_equipment, font_type, font_size = getFontSetup(
        image_data[9]
    )

    # calculate textbox size
    textbox_size_settings = draw.multiline_textbbox(
        (0, 0), image_data[7], font=font_setup_capture_data
    )
    textbox_size_equipment = draw.multiline_textbbox(
        (0, 0), image_data[8], font=font_setup_equipment
    )

    # if text is too big, make it smaller
    while textbox_size_equipment[2] > image_data[9][0]:
        font_size = font_size * 0.9
        font_setup_equipment = ImageFont.truetype(font_type, size=font_size)
        textbox_size_equipment = draw.multiline_textbbox(
            (0, 0), image_data[8], font=font_setup_equipment
        )

    empty_image.close()

    return (
        textbox_size_settings,
        textbox_size_equipment,
        font_setup_capture_data,
        font_setup_equipment,
    )


####################################
# print exif data
# data: exif data
# image_name: name of image
# returns nothing
def printImageData(data, image_name):
    print("Exif data for", image_name)
    print("Camera:", data[0])
    print("Lens:", data[1])
    print(
        data[2],
        "mm ",
        "f/",
        data[3],
        " ISO ",
        data[5],
        " ",
        getShutterSpeedFormat(data[4]),
        " sec",
        sep="",
    )


#########################################
# GET DATA
# main function to get exif data and create image
# called in main function
# returns nothing
# image_name: name of image to get exif data from
#########################################
def getExifImage(image_name):
    # get exif data
    image_data = getImageData(image_name)
    printImageData(image_data, image_name)

    # create blured image
    output_image = Image.open(image_name)
    output_image = output_image.filter(ImageFilter.GaussianBlur(radius=50))

    # create image draw object
    image_draw = ImageDraw.Draw(output_image, "RGBA")

    # calculate textbox size
    (
        textbox_size_capture_data,
        textbox_size_equipment,
        font_setup_capture_data,
        font_setup_equipment,
    ) = calculateTextboxSize(image_data)

    # calculate text position
    text_position_capture_data_string = calulateTextPosition(
        image_data[9], textbox_size_capture_data[2], textbox_size_capture_data[3]
    )
    text_position_equipment_string = calulateTextPosition(
        image_data[9], textbox_size_equipment[2], textbox_size_equipment[3]
    )

    # check if text and background should be white or black
    color_list = getColorForTextandBackground(output_image)

    # draw a semitransparent rectangle over whole image
    image_draw.rectangle((0, 0, image_data[9][0], image_data[9][1]), fill=color_list[1])

    # draw text
    image_draw.text(
        (
            text_position_capture_data_string[0],
            text_position_capture_data_string[1] * 0.4,
        ),
        image_data[7],
        font=font_setup_capture_data,
        fill=color_list[0],
        align="center",
        spacing=30,
    )
    image_draw.text(
        (text_position_equipment_string[0], text_position_equipment_string[1] * 1.7),
        image_data[8],
        font=font_setup_equipment,
        fill=color_list[0],
        align="center",
        spacing=30,
    )

    # save image
    output_image.show()
    output_image.save(image_name.replace(".jpg", "") + "_blur_with_text.jpg")

    # close image instance
    output_image.close()


#########################################
# MAIN
#########################################
if __name__ == "__main__":
    # open folder
    folder = str(argv[1])
    # getExifImage(folder)

    # list all files in folder
    files = os.listdir(folder)
    print(files)

    # loop through all files
    for file in files:
        # check if file is a jpg
        if file.endswith(".jpg") or file.endswith(".jpeg"):
            # get exif data
            getExifImage(folder + "/" + file)
        else:
            print("nothing to do here ", file)
