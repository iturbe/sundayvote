from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
from os import listdir
from os.path import isfile, join
import json
import re
import textwrap
import copy
# import blend_modes

# *** VARIABLES ***
raw_resources_path = "resources/"

# logo modifiers
vote_box = False
invert_logo = False
pride_logo = False
tweaked_logo = True # std logo + gaussian & gradient

current_color_overlay = 99

# COVER
cover_darken = False # whether a 50% darkening is applied to the cover or not
cover_color_overlay = True # whether the color overlay is applied to the cover
cover_color_overlay_strength = .5 # % of hardness of the cover color overlay

# title
line_1 = "THIS WILL"
line_2 = "CREATE A"
line_3 = "COOL TITLE"
line_4 = "EFFECT"
titleTexts = [line_1, line_2, line_3, line_4]

# VOTE
color_overlay_strength = .3 # % hardness of the cover color overlay
split_overlay_strength = .1 # % hardness of the split color overlay

# AFTER VOTE
av_color_overlay = True # whether the color overlay is applied to the AV
av_color_overlay_strength = .5 # % of hardness of the AV color overlay
av_darken_10 = False # whether a 10% darkening is applied to the AV or not
av_darken_20 = False # whether a 20% darkening is applied to the AV or not
av_darken_50 = False # whether a 50% darkening is applied to the AV or not

#IMPORTANT: ONLY APPLIES TO SINGLE-IMAGES
blurEverything = False # applies a gaussian filter to every image for passing on to the analyst
gaussian_strength = 10 # how much of a blur to apply


# TODO: “How to Write Python Command-Line Interfaces like a Pro” by Simon Hawe https://link.medium.com/tV8DZyP0n3

# TODO: “Learn How to Quickly Create UIs in Python” by Costas Andreou https://link.medium.com/DlZS2ZT0W2

# TODO: UI flow: choose type of post, fill up JSON
# will definitely need to re-think the JSON format we currently use

# *** FUNCTIONS ***

# Setup function that loads the JSON data and the raw resources
def setup():
    print("Loading preferences, tweaks and raw resources")
    print("Currently selected color_overlay: ", current_color_overlay)
    print("color_overlay_strength:", color_overlay_strength)
    print("split_overlay_strength:", split_overlay_strength)

    # load preferences
    with open('preferences.json') as json_file:
        prefs = json.load(json_file)

    # load vote-by-vote tweaks
    with open('tweaks.json') as json_file:
        tweaks = json.load(json_file)

    # load resources
    images = [f for f in listdir(raw_resources_path) if isfile(join(raw_resources_path, f))]
    images.sort()
    print(images)

    return prefs, tweaks, images

# breaks up the given text into a multiline
# return: a text array
def make_multiline(input_text, character_wrap):

    # check for paragraph breaks
    split_content = input_text.split(" | ")

    # insert empty lines
    spaced_content = ["SKIP THIS LINE"] * (len(split_content) * 2 - 1)
    spaced_content[0::2] = split_content

    # print("sc")
    # print(spaced_content)

    content_final = []

    for spaced in spaced_content:
        
        if spaced == "SKIP THIS LINE":
            content_final.append(" ")
        
        else:
            content_final += textwrap.wrap(spaced, width=character_wrap)

    # print("cf")
    # print(content_final)

    return content_final

def resizeImage(inputImg, targetWidth, targetHeight):
    """
    Calculates the resize ratios for adjusting an image's size.

    Parameters
    ----------
    inputImg : The image to resize
    targetWidth : The desired width
    targetHeight : The desired height

    Returns
    ----------
    resizedImg : The image, resized
    offset : The x-coord offset for placing the image centered on the canvas
    """
    offset = 0
    wasExact = True
    if inputImg.size[0] != targetWidth and inputImg.size[1] != targetHeight:
    
        # calculate ratio & resulting width with height priority
        resize_ratio = inputImg.size[0] / inputImg.size[1]
        new_width = targetHeight * resize_ratio

        # resize image 
        inputImg = inputImg.resize((int(new_width), targetHeight), Image.ANTIALIAS)

        # check to see if the image is wide enough
        if inputImg.width < targetWidth:
            # recalculate dimensions with width priority
            resize_ratio2 = inputImg.size[1] / inputImg.size[0]
            new_height = targetWidth * resize_ratio2
            # resize accordingly
            inputImg = inputImg.resize((targetWidth, int(new_height)), Image.ANTIALIAS)
            new_width = targetWidth

        # calculate offset to center image on canvas
        offset = int((new_width - targetWidth)/2)
        wasExact = False

    else:
        print("Resource image was exactly target size, skipping reizing...")

    return inputImg, offset, wasExact

def makeTitle():
    """
    Uses the predetermined strings to make the title image.
    """
    # variable setup
    title = Image.new('RGBA', (1125, 1125), (0, 0, 0, 0))

    # object creation
    draw = ImageDraw.Draw(title)
    
    # place elements on the image
    # draw.ellipse((25, 25, 75, 75), fill=(255, 0, 0))
    fnt = ImageFont.truetype('../fonts/LemonMilk.otf', tweaks['text_prefs']['titleText_font_size'])
    title_color = tweaks['text_prefs']['titleText_font_color']

    # the a factor that allows us to space the lines evenly
    y_starter = 275
    y_constant = 150
    x_margin = 140
    centered = 845

    line_to_text_margin = 15

    # multiline print
    for idx, line in enumerate(titleTexts):
        
        # get the line's dimensions
        width, height = fnt.getsize(line)
        
        # calculate the text's y position
        if idx == 0:
            y_coord = y_starter
        else:
            y_coord = y_coord + y_constant

        # calculate the text's x position
        x_coord = x_margin + (centered - width)
        
        # calculate the line's coordinates
        x0 = x_margin
        y0 = y_coord + (height/4) * 1.75
        x1 = x_coord - line_to_text_margin
        y1 = y_coord + (height/4) * 3
        
        # actually draw the line
        draw.rectangle([x0, y0, x1, y1], fill="#000000")
        
        # actually draw the text
        draw.text((x_coord, y_coord), line, font=fnt, fill=title_color, stroke_width=1, stroke_fill="#000000")

    # duplicate the image
    actual_text = title.__copy__()
    
    # invert RGBA image
    r,g,b,a = actual_text.split()
    rgb_image = Image.merge('RGB', (r,g,b))
    inverted_image = ImageOps.invert(rgb_image)
    r2,g2,b2 = inverted_image.split()
    white_text = Image.merge('RGBA', (r2,g2,b2,a))
    # white_text.save(raw_resources_path+'titleA.png', 'PNG')

    # blur the bg of the image 
    gaussian = title.filter(ImageFilter.GaussianBlur(radius=10))
    # gaussian.save(raw_resources_path+'titleB.png')
    # actual_text.save(raw_resources_path+'titleB.png', 'PNG')

    gaussian.paste(white_text, (0, 0), white_text)
    
    # actually save the image to file
    gaussian.save(raw_resources_path+'title.png', 'PNG')

    return gaussian

# makes the cover & results images
def make_cover(canvas, img_name):
    cover_bg = Image.open(raw_resources_path + img_name)
    
    # old
    logo = Image.open('std_resources/logo.png')

    # the future is now old man
    logo = Image.open('std_resources/logo_2020_white.png')
    
    if invert_logo:
        logo = Image.open('std_resources/logo_2020_black.png')

    if pride_logo:
        logo = Image.open('std_resources/logo_pride.png')

    if tweaked_logo:
        logo = Image.open('std_resources/logo_2020_tweaked.png')
    
    ## check if we have a custom title or we need to create our own
    # does a custom file exist?
    title = ""
    if isfile(raw_resources_path+'title.png'):
        title = Image.open(raw_resources_path+'title.png')

    else:
        # naw, we gotta make our own
        title = makeTitle()
    
    results = Image.open('std_resources/results.png')
    # av_logo = Image.open('std_resources/aftervote_white.png')
    av_logo = Image.open('std_resources/aftervote_2021.png')
    
    resizedImg, offset, wasExact = resizeImage(cover_bg, prefs['width_full'], prefs['height_full'])
    
    # # if the image is exactly the dimensions, skip it
    # if cover_bg.size[0] != prefs['width_full'] and cover_bg.size[1] != prefs['height_full']:

    #     # calculate ratios
    #     resize_ratio = cover_bg.size[0] / cover_bg.size[1]
    #     new_width = prefs['height'] * resize_ratio

    #     # resize image 
    #     cover_bg = cover_bg.resize((int(new_width), prefs['height']), Image.ANTIALIAS)

    #     # check to see if the image is large enough
    #     if cover_bg.width < prefs['width_full']:
    #         # recalculate dimensions
    #         resize_ratio2 = cover_bg.size[1] / cover_bg.size[0]
    #         new_height = prefs['width_full'] * resize_ratio2
    #         # resize with width priority
    #         cover_bg = cover_bg.resize((prefs['width_full'], int(new_height)), Image.ANTIALIAS)
    #         new_width = prefs['width_full']

    #     # calculate offset to center image on canvas
    #     offset = int((new_width - prefs['width'])/2)

    # paste bg on canvas
    if wasExact:
        canvas.paste(cover_bg, (0, 0))
    else:
        canvas.paste(resizedImg, (0-offset, prefs['guide_top']))
    
    # else:
    #     print("Resource image was exactly canvas size, skipping reizing...")
    #     canvas.paste(cover_bg, (0, 0))

    # *** COLOR OVERLAY ***
    if cover_color_overlay:
        overlay = Image.open('std_resources/color_overlay'+str(current_color_overlay)+'.jpg').resize(canvas.size, resample=Image.BICUBIC)
        canvas = Image.blend(canvas, overlay, cover_color_overlay_strength)

    # export the precover
    canvas.save('output/PRECOVER.png',  dpi=(300.0, 300.0))

    # make the av
    for_av = canvas.__copy__()
    for_av.paste(av_logo, (0,0), av_logo)
    for_av.save('output/AV.png',  dpi=(300.0, 300.0))

    # *** DARKEN OVERLAY ***
    if cover_darken:
        overlay = Image.open('std_resources/darken_20.png')
        canvas.paste(overlay, (0, 0), overlay)

    # paste SV logo on canvas
    canvas.paste(logo, (0, 0), logo)

    # paste SV title on canvas
    canvas.paste(title, (int((prefs['width_full']-title.size[0])/2), prefs['guide_middle'] + int((prefs['half_height']-title.size[1])/2)), title)
    
    # export
    canvas.save('output/COVER.png',  dpi=(300.0, 300.0))

    # paste "results" text on canvas
    # canvas.paste(results, (0, 0), results)

    # export results pic
    # canvas.save('output/RESULTS.png',  dpi=(300.0, 300.0))

    return canvas

# makes the aftervote images
def make_afterVote(canvas, img_name):
    av_bg = Image.open(raw_resources_path + img_name)
    
    # black
    av_logo = Image.open('std_resources/aftervote_black.png')
    
    if invert_logo:
        av_logo = Image.open('std_resources/aftervote_white.png')
    
    # if the image is exactly the dimensions, skip it
    if av_bg.size[0] != prefs['width_full'] and av_bg.size[1] != prefs['height_full']:

        # calculate ratios
        resize_ratio = av_bg.size[0] / av_bg.size[1]
        new_width = prefs['height'] * resize_ratio

        # resize image 
        av_bg = av_bg.resize((int(new_width), prefs['height']), Image.ANTIALIAS)

        # check to see if the image is large enough
        if av_bg.width < prefs['width_full']:
            # recalculate dimensions
            resize_ratio2 = av_bg.size[1] / av_bg.size[0]
            new_height = prefs['width_full'] * resize_ratio2
            # resize with width priority
            av_bg = av_bg.resize((prefs['width_full'], int(new_height)), Image.ANTIALIAS)
            new_width = prefs['width_full']

        # calculate offset to center image on canvas
        offset = int((new_width - prefs['width'])/2)

        # paste bg on canvas
        canvas.paste(av_bg, (0-offset, prefs['guide_top']))
    
    else:
        print("Resource image was exactly canvas size, skipping reizing...")
        canvas.paste(av_bg, (0, 0))

    # *** COLOR OVERLAY ***
    if av_color_overlay:
        overlay = Image.open('std_resources/color_overlay'+str(current_color_overlay)+'.jpg').resize(canvas.size, resample=Image.BICUBIC)
        canvas = Image.blend(canvas, overlay, av_color_overlay_strength)

    # *** DARKEN OVERLAYS ***
    if av_darken_10:
        overlay = Image.open('std_resources/darken_10.png')
        canvas.paste(overlay, (0, 0), overlay)
    
    if av_darken_20:
        overlay = Image.open('std_resources/darken_20.png')
        canvas.paste(overlay, (0, 0), overlay)
    
    if av_darken_50:
        overlay = Image.open('std_resources/darken_50.png')
        canvas.paste(overlay, (0, 0), overlay)

    # paste SV logo on canvas
    canvas.paste(av_logo, (0, 0), av_logo)
    
    # export results pic
    canvas.save(f'output/av_{img_name}.png',  dpi=(300.0, 300.0))

    return canvas

# makes a standard image given a single image as a bg
def make_singleImg(canvas, img_name, image_number):
    single_img = Image.open(raw_resources_path + img_name)

    # if the image is exactly the dimensions, skip it
    if single_img.size[0] != prefs['width_full'] and single_img.size[1] != prefs['height_full']:

        # calculate ratios
        resize_ratio = single_img.size[0] / single_img.size[1]
        new_width = prefs['height'] * resize_ratio

        # resize image 
        single_img = single_img.resize((int(new_width), prefs['height']), Image.ANTIALIAS)

        # check to see if the image is large enough
        if single_img.width < prefs['width_full']:
            # recalculate dimensions
            resize_ratio2 = single_img.size[1] / single_img.size[0]
            new_height = prefs['width_full'] * resize_ratio2
            # resize with width priority
            single_img = single_img.resize((prefs['width_full'], int(new_height)), Image.ANTIALIAS)
            new_width = prefs['width_full']

        # calculate offset to center image on canvas
        offset = int((new_width - prefs['width'])/2)

        # paste bg on canvas
        canvas.paste(single_img, (0-offset, prefs['guide_top']))
        # canvas.paste(single_img, (0-offset, 0))
    
    else:
        print("Resource image was exactly canvas size, skipping reizing...")
        canvas.paste(single_img, (0, 0))
    
    if image_number in tweaks['gaussianBlur'] or blurEverything:
        print("Blurring image #", image_number)
        canvas = canvas.filter(ImageFilter.GaussianBlur(gaussian_strength))

    return canvas

# makes a standard image given two images as the bg
def make_dualImg(canvas, img_name, image_number):

    # *** FIRST IMAGE *** 
        
    # get the filelist from the os
    split_images = [f.split('.') for f in listdir(raw_resources_path)]
    # filter to get only the one we want
    filtered = [f for f in split_images if f[0] == str(image_number)+'a']
    # filtered now contains only the image we want, but in a list of 1 item
    actual_img = filtered[0][0] + '.' + filtered[0][1]
    # open image
    first_img  = Image.open(raw_resources_path+actual_img)
    
    # calculate ratios
    resize_ratio = first_img.size[0] / first_img.size[1]
    new_width = prefs['half_height'] * resize_ratio
    # resize image 
    first_img = first_img.resize((int(new_width), prefs['half_height']), Image.ANTIALIAS)

    # check to see if the image is large enough
    if first_img.width < prefs['width_full']:
        # recalculate dimensions
        resize_ratio2 = first_img.size[1] / first_img.size[0]
        new_height = prefs['width_full'] * resize_ratio2
        # resize with width priority
        first_img = first_img.resize((prefs['width_full'], int(new_height)), Image.ANTIALIAS)
        new_width = prefs['width_full']

    # calculate offset to center image on canvas
    offset = int((new_width - prefs['width'])/2)
    # paste 1st img on canvas
    canvas.paste(first_img, (0-offset, prefs['guide_top']))

    # *** SECOND IMAGE ***
    # get the filelist from the os
    split_images = [f.split('.') for f in listdir(raw_resources_path)]
    # filter to get only the one we want
    filtered = [f for f in split_images if f[0] == str(image_number)+'b']
    # filtered now contains only the image we want, but in a list of 1 item
    actual_img = filtered[0][0] + '.' + filtered[0][1]
    # open image
    second_img = Image.open(raw_resources_path+actual_img)
    
    # calculate ratios
    resize_ratio = second_img.size[0] / second_img.size[1]
    new_width = prefs['half_height'] * resize_ratio
    # resize image 
    second_img = second_img.resize((int(new_width), prefs['half_height']), Image.ANTIALIAS)

    # check to see if the image is large enough
    if second_img.width < prefs['width_full']:
        # recalculate dimensions
        resize_ratio2 = second_img.size[1] / second_img.size[0]
        new_height = prefs['width_full'] * resize_ratio2
        # resize with width priority
        second_img = second_img.resize((prefs['width_full'], int(new_height)), Image.ANTIALIAS)
        new_width = prefs['width_full']

    # calculate offset to center image on canvas
    offset = int((new_width - prefs['width'])/2)
    # paste 2nd img on canvas
    canvas.paste(second_img, (0-offset, prefs['guide_middle']))
    
    return canvas

# adds the necessary overlays to the image given the speicifcations in preferences
def addOverlays(canvas, image_number):
    
    # *** SPLIT OVERLAY ***
    if image_number in tweaks['split']:
        # overlay = Image.open('std_resources/diagonal_soft.png')
        # canvas.paste(overlay, (0, 0), overlay)

        # overlay = Image.open('std_resources/diagonal_soft.jpg')
        overlay = Image.open('std_resources/diagonal_2021.jpg')
        canvas = Image.blend(canvas, overlay, split_overlay_strength)

    # *** COLOR OVERLAY ***
    if image_number in tweaks['color_overlay']:
        overlay = Image.open('std_resources/color_overlay'+str(current_color_overlay)+'.jpg').resize(canvas.size, resample=Image.BICUBIC)
        canvas = Image.blend(canvas, overlay, color_overlay_strength)
        # result.show()
        # canvas.paste(overlay, (0, 0), overlay)

    # *** 10% DARKEN OVERLAY ***
    if image_number in tweaks['darken_10']:
        overlay = Image.open('std_resources/darken_10.png')
        canvas.paste(overlay, (0, 0), overlay)
    
    # *** 20% DARKEN OVERLAY ***
    if image_number in tweaks['darken_20']:
        overlay = Image.open('std_resources/darken_20.png')
        canvas.paste(overlay, (0, 0), overlay)

    # *** 50% DARKEN OVERLAY ***
    if image_number in tweaks['darken_50']:
        overlay = Image.open('std_resources/darken_50.png')
        canvas.paste(overlay, (0, 0), overlay)

    # *** VOTE BOX OVERLAY ***
    if vote_box:
        overlay = Image.open('std_resources/vote_box.png')
        canvas.paste(overlay, (0, 0), overlay)

    return canvas

# main function, makes an image out of its path and a selector (0, 1, 2, 3)
# 0 - cover pic
# 1 - single image
# 2 - two images
# 3 - after vote
def make_image(img_name, which_type):

    # img_name_full = '.'.join(img_name)
    split_image = img_name.split('.')
    image_number = int(split_image[0].strip('a').strip('b'))

    #debug
    print("Incoming image:", image_number)

    # setup canvas
    canvas = Image.new('RGB', (prefs['width_full'], prefs['height_full']), color='black')

    # actually make the images

    # cover pic
    if which_type == 0:
        canvas = make_cover(canvas, img_name)
    
    # one single image
    elif which_type == 1:
        canvas = make_singleImg(canvas, img_name, image_number)
    
    # two images
    elif which_type == 2:
        canvas = make_dualImg(canvas, img_name, image_number)

    # after vote (is always a single img)
    elif which_type == 3:
        canvas = make_afterVote(canvas, img_name, image_number)
        
    # error
    else:
        print("Call to make_image with illegal params:", img_name, which_type)

    # add overlays
    canvas = addOverlays(canvas, image_number)

    # TODO: update the blending mode with this: https://pypi.org/project/blend-modes/
    # TODO: figure out the best way to store the data in the JSON object in order to mimick a . type element accessing
    # TODO: figure out emojis
    # TODO: is this relevant? https://gist.github.com/turicas/1455973

    # *** TEXT ***
    if image_number in tweaks['titleText']:

        # TEXT contains the image numbers that have text
        # CONTENT contains, in the same order, the text for each image (in order)

        # get the array position of the image number we want to work with
        array_position = tweaks["titleText"].index(image_number)
        print("arraypos:", array_position)

        d = ImageDraw.Draw(canvas)

        # paste the title darkener
        title_dark_box = Image.open('std_resources/title_darken.png')
        canvas.paste(title_dark_box, (0, 0), title_dark_box)

        # ** TITLE **
        
        # set the font & color
        # fnt = ImageFont.truetype(tweaks['text_prefs']['title_font'], tweaks['text_prefs']['title_font_size'])
        fnt = ImageFont.truetype('../fonts/LemonMilk.otf', tweaks['text_prefs']['title_font_size'])
        title_color = tweaks['text_prefs']['title_color']

        # multiline the title
        title = make_multiline(tweaks['content'][array_position][0], tweaks['text_prefs']['title_font_wrap'])

        # load the offset
        title_y_offset = tweaks['text_prefs']['title_y_offset']

        # multiline print
        for line in title:
            title_width, height = fnt.getsize(line)
            x_coord_title = (prefs['width_full'] - title_width) / 2
            d.text((x_coord_title, title_y_offset), line, font=fnt, fill=title_color)
            title_y_offset += height

        # ** CONTENT **
        
        # set the font
        # fnt = ImageFont.truetype(tweaks['text_prefs']['content_font'], tweaks['text_prefs']['content_font_size'])
        fnt = ImageFont.truetype('../fonts/LemonMilk.otf', tweaks['text_prefs']['content_font_size'])

        # multiline the content
        content = make_multiline(tweaks['content'][array_position][1], tweaks['text_prefs']['content_font_wrap'])
        
        # starting y coord for the first line of text
        y_coord = tweaks['text_prefs']['content_spacer_top']

        # set colors
        emphasis_color = tweaks['text_prefs']['emphasis_color']
        normal_color = tweaks['text_prefs']['normal_color']
        
        for line in content:

            # check to see if we have one or more emphasis words in the line
            if "¬" in line:

                # split the line based on spaces
                split_line = line.split(" ")
                # print(split_line)

                split_line_new = split_line.copy()

                # aux to save which positions we gonna be emphasizing
                which_words = []

                for idx, word in enumerate(split_line):
                    
                    # check for the character
                    if "¬" in word:
                        
                        # clean words
                        split_line_new[idx] = word[1:]

                        # indicate which words we gonna emphasize
                        which_words.append(True)
                    
                    else:
                        which_words.append(False)
                    
                    # if we're not at the last one, add a space
                    if idx < len(split_line) - 1:
                        split_line_new[idx] = split_line_new[idx] + " "
                    
                #debug
                # print("HERE:", split_line_new)
                
                # aux variables
                widths = []
                heights = []
                
                # add all the words' widths
                for idx, word in enumerate(split_line_new):
                
                    # calculate each word's width
                    width, height = fnt.getsize(word)
                    # print("word:", word, "w:", width, "h:", height)
                    widths.append(width)
                    heights.append(height)

                # calculate line width
                full_sentence = ''.join(split_line_new)
                width, height = fnt.getsize(full_sentence)
                
                # the sum of each line's width should be the same as the entire line computed together
                # print("sentence:", ">" + full_sentence + "<", "w:", width, "h:", height)
                # print("sum:", sum(widths))

                # calculate the offset of the entire sentence
                x_coord = (prefs['width_full'] - width) / 2

                # cycle the entire sentence, individually placing each word
                for idx, word in enumerate(split_line_new):

                    # check to see if we're on an emphasized word
                    if which_words[idx]:

                        #TODO: - multiple word colors
                        
                        # colored word
                        d.text((x_coord, y_coord), word, font=fnt, fill=emphasis_color)
                    
                    else:
                        # normal word
                        d.text((x_coord, y_coord), word, font=fnt, fill=normal_color)

                    # increase the x_offset
                    x_coord += widths[idx]

                # clean the words
                # split_line_clean = [x[1:] for x in split_line if "¬" in x]
                # print(split_line_clean)
            
            else:

                # no fuss needed
                width, height = fnt.getsize(line)
                
                # calculate the x_coord
                x_coord = (prefs['width_full'] - width) / 2
            
                # write the line
                d.text((x_coord, y_coord), line, font=fnt)
            
            # regardless, increase y_coord for next line
            y_coord += height
    
    # *** 2-OPTION TEXT ***
    if image_number in tweaks['dual']:

        # get the array position of the image number we want to work with
        array_position = tweaks["dual"].index(image_number)

        d = ImageDraw.Draw(canvas)

        # ** CONTENT **
        
        # set the font
        # fnt = ImageFont.truetype('../fonts/LemonMilk.otf', tweaks['text_prefs']['content_font_size'])
        # fnt = ImageFont.truetype('../fonts/Helvetica-Neue-Bold.ttf', tweaks['text_prefs']['content_font_size'])
        fnt = ImageFont.truetype('../fonts/Helvetica-Neue-Bold.ttf', tweaks['text_prefs']['content_font_size_large'])
        fnt = ImageFont.truetype('../fonts/CircularStd-Bold.otf', tweaks['text_prefs']['content_font_size_large'])
        

        # get both contents and multiline them
        top_content = make_multiline(tweaks['dualcontent'][array_position][0], tweaks['text_prefs']['content_font_wrap_large'])
        bottom_content = make_multiline(tweaks['dualcontent'][array_position][1], tweaks['text_prefs']['content_font_wrap_large'])        
        
        # BAD
        # starting y coord for the first line of text
        top_y_coord = tweaks['text_prefs']['content_spacer_top_option']
        bottom_y_coord = tweaks['text_prefs']['content_spacer_bottom_option']

        # TODO: GOOD
        # TODO: MAKE BOTH TEXTS HAVE THE SAME STLE AS THE NEW SUNDAY VOTE OPTIONS (XMAS VOTE)
        
        # calculate the starting position based on how much text there is
        width, height = fnt.getsize(top_content[0]) # we actually only getting the height here
        total_content_height = height * len(top_content) # multiply by how many lines there are
        # print("ltc:", len(top_content))
        print("tch:", total_content_height)
        
        top = prefs['guide_top']
        middle = prefs['guide_middle']
        total_height = middle-top
        print("th:", total_height)

        y_coord = prefs['guide_top'] - (total_content_height/2) + ((total_height - total_content_height)/2) # this should, in theory, be smack in the middle

        # set colors
        emphasis_color = tweaks['text_prefs']['emphasis_color']
        normal_color = tweaks['text_prefs']['normal_color']
        
        border = True # whether we paint the green and deeppink outlines on the words or not
        border_thickness = 5 # border thickness, in px
        
        # top content
        for line in top_content:

            # print normally
            width, height = fnt.getsize(line)
            
            # calculate the x_coord
            x_coord = (prefs['width_full'] - width) / 2

            # check to see if we want a border
            if border:
                d.text((x_coord-border_thickness, y_coord), line, font=fnt, fill="green")
                d.text((x_coord+border_thickness, y_coord), line, font=fnt, fill="green")
                d.text((x_coord, y_coord-border_thickness), line, font=fnt, fill="green")
                d.text((x_coord, y_coord+border_thickness), line, font=fnt, fill="green")
        
            # write the line
            d.text((x_coord, y_coord), line, font=fnt, fill=normal_color)
        
            # increase y_coord for next line
            y_coord += height

        normal_color = tweaks['text_prefs']['normal_color']
        
        # bottom content
        for line in bottom_content:

            # print normally
            width, height = fnt.getsize(line)
            
            # calculate the x_coord
            x_coord = (prefs['width_full'] - width) / 2

            # check to see if we want a border
            if border:
                d.text((x_coord-border_thickness, bottom_y_coord), line, font=fnt, fill="deeppink")
                d.text((x_coord+border_thickness, bottom_y_coord), line, font=fnt, fill="deeppink")
                d.text((x_coord, bottom_y_coord-border_thickness), line, font=fnt, fill="deeppink")
                d.text((x_coord, bottom_y_coord+border_thickness), line, font=fnt, fill="deeppink")
        
            # write the line
            d.text((x_coord, bottom_y_coord), line, font=fnt, fill=normal_color)
        
            # increase y_coord for next line
            bottom_y_coord += height
    
    # *** QUESTIONS ***
    if image_number in tweaks['whichQuestions']:

        # get the array position of the image number we want to work with
        array_position = tweaks["whichQuestions"].index(image_number)
        print("arraypos:", array_position)

        # has to be RGBA in order for the transparency to work
        d = ImageDraw.Draw(canvas, 'RGBA')

        # *** TITLE *** 

        # TODO: hacer top/bottom text dinámico basado en el offset

        # *** CONTENT *** 
        
        # set the font & color
        fnt = ImageFont.truetype('../fonts/CircularStd-Bold.otf', tweaks['text_prefs']['question_font_size'])
        question_color = tweaks['text_prefs']['question_color']

        # multiline the text
        question = make_multiline(tweaks['questions'][array_position], tweaks['text_prefs']['question_font_wrap'])

        # load the offset
        question_y_offset = tweaks['text_prefs']['question_y_offset']

        # top and bottom margins for the question title darkener, in px
        # for some reason the bottom margin is shorter...?
        top_question_margin    = 25
        bottom_question_margin = top_question_margin

        # 0-100%
        transparency = 0.75
        trans = int(255*transparency)
        question_darkener = (0, 0, 0, trans)

        # debug
        # question_width, height = fnt.getsize(question[0])
        # print("base:", height)

        # calculate the question box's dimensions
        # CANNOT calculate the height like this since each line's height varies if not all caps
        # total_height = height*len(question)
        total_height = 0
        for line in question:
            question_width, thisheight = fnt.getsize(line)
            total_height += thisheight

        # actually draw the question box
        d.rectangle((0, question_y_offset-top_question_margin, prefs['width_full'], question_y_offset+total_height+bottom_question_margin), fill=question_darkener)

        # question text outline
        border = True
        border_thickness = 5 # in px
        border_color = "black"

        # multiline print
        for idx, line in enumerate(question):
            question_width, height = fnt.getsize(line)
            # print("dynamic:", height)
            x_coord_title = (prefs['width_full'] - question_width) / 2

            if border:
                d.text((x_coord_title-border_thickness, question_y_offset), line, font=fnt, fill=border_color)
                d.text((x_coord_title+border_thickness, question_y_offset), line, font=fnt, fill=border_color)
                d.text((x_coord_title, question_y_offset-border_thickness), line, font=fnt, fill=border_color)
                d.text((x_coord_title, question_y_offset+border_thickness), line, font=fnt, fill=border_color)
            
            # write the text
            d.text((x_coord_title, question_y_offset), line, font=fnt, fill=question_color)

            question_y_offset += height
    
    # export
    canvas.save('output/' + str(image_number) + '.png',  dpi=(300.0, 300.0))
    
# load preferences, tweaks and raw resources
prefs, tweaks, images = setup()

# actual main
if __name__ == "__main__":

    # aux for b-side cases
    skip = False

    for image in images:

        # b-sides
        if skip:
            skip = False
            continue

        # split based on extension period
        name = image.split('.')

        # print(image)
        # print(name)

        # # case 1: two images
        if(re.search("a$", name[0])):
            # print("case 1:", name)
            skip = True # skip next iteration since it will be the second image
            make_image(image, 2)

        # case 2: cover (+ results)
        elif(re.search("^0$", name[0])):
            # print("case 3:", name)
            make_image(image, 0)
        
        # case 3: one image
        elif(re.search("^[0-9]+$", name[0])):
            # print("in:", name)
            make_image(image, 1)

        # case 4: after vote
        elif(re.search("^av", name[0])):
            # print("case 3:", name)
            make_image(image, 3)

        else:
            print("Image name not recognized:", image)
