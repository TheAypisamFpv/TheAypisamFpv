from math import ceil
import cv2
import numpy as np
from PIL import Image

# Parameters
videoPath = "Bad Apple.mp4"  # Path to the input video
outputGif = "Bad Apple.gif"  # Name of the generated GIF

gifHeight = 7  # commit pixel
gifWidth = 52  # commit pixel
frameSkip = 2  # Number of frames to skip to speed up animation

# GitHub pixels paths
githubPixelsPaths = ["pixels/pixel0.png", "pixels/pixel1.png", "pixels/pixel2.png", "pixels/pixel3.png", "pixels/pixel4.png"]
githubSubPixelsPaths = ["subPixels/pixel0.png", "subPixels/pixel1.png", "subPixels/pixel2.png", "subPixels/pixel3.png", "subPixels/pixel4.png"]
pixelNum = len(githubPixelsPaths)

# Load the pixel images
githubPixels = [Image.open(path) for path in githubPixelsPaths]
pixelWidth = githubPixels[0].width
pixelHeight = githubPixels[0].height

githubSubPixels = [Image.open(path) for path in githubSubPixelsPaths]
subPixelWidth = githubSubPixels[0].width
subPixelHeight = githubSubPixels[0].height



# Load the video
cap = cv2.VideoCapture(videoPath)
frames = []
frameCount = 0

videoLenght = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
videoFps = cap.get(cv2.CAP_PROP_FPS)

print("Processing Video...", end="\r")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Resize the frame while maintaining aspect ratio
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    aspectRatio = frame.shape[1] / frame.shape[0]
    scale = 2
    scaledFrameWidth = int(gifHeight * aspectRatio) * scale
    scaledFrameHeight = gifHeight * scale
    
    # Normalize pixels
    normalizedFrame = np.clip(frame / 255 * pixelNum-1, 0, pixelNum-1)
    normalizedResizedFrame = cv2.resize(normalizedFrame, (scaledFrameWidth, scaledFrameHeight), interpolation=cv2.INTER_AREA)
    
    frames.append(normalizedResizedFrame)
    
    frameCount += 1
    if frameCount % frameSkip != 0:
        frames.pop()

    print(f"Processed Video frame {frameCount + 1}/{videoLenght}          ", end="\r")

cap.release()

print("Processing Video Done             \n")


def getIntensities(frameQuad):
    intensities = []
    for y in range(2):
        for x in range(2):
            intensity = round(frameQuad[y, x])
            intensities.append(intensity)
    
    return intensities

def getSubPixels(intensities: list):
    pixelmate = np.zeros((pixelHeight, pixelWidth, 3), dtype=np.uint8)
    
    for i, intensity in enumerate(intensities):

        intensity = min(intensity, pixelNum-1)
        
        subPixelImg = githubSubPixels[intensity].convert("RGB")
        subPixelImg = subPixelImg.resize((subPixelWidth, subPixelHeight))
        # print(intensity, i)
        if i == 0:
            # add the subpixel to the pixelmate at the top left corner
            pixelmate[0:subPixelHeight, 0:subPixelWidth] = subPixelImg
        elif i == 1:
            # rotate the subpixel -90 degrees
            subPixelImg = subPixelImg.rotate(-90)
            # add the subpixel to the pixelmate at the top right corner
            pixelmate[0:subPixelHeight, pixelWidth-subPixelWidth:pixelWidth] = subPixelImg
        elif i == 2:
            # rotate the subpixel 90 degrees
            subPixelImg = subPixelImg.rotate(90)
            # add the subpixel to the pixelmate at the bottom left corner
            pixelmate[pixelHeight-subPixelHeight:pixelHeight, 0:subPixelWidth] = subPixelImg
        elif i == 3:
            # rotate the subpixel 180 degrees
            subPixelImg = subPixelImg.rotate(180)
            # add the subpixel to the pixelmate at the bottom right corner
            pixelmate[pixelHeight-subPixelHeight:pixelHeight, pixelWidth-subPixelWidth:pixelWidth] = subPixelImg


    # view the pixelmate as debug
    # cv2.imshow("pixelmate", pixelmate)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return pixelmate




# Generate the initial random commit pixels with a bias towards pixel0
initialPixels = np.clip(np.random.normal(0, 1.5, (gifHeight, gifWidth)), 0, pixelNum-1).astype(int)

# Initialize pixelReplaced array
pixelReplaced = np.zeros((gifHeight, gifWidth), dtype=int)

# Create the GIF
imgFrames = []
for i, frame in enumerate(frames):
    # Create a new image filled with pixel0
    pixel0 = githubPixels[0].convert("RGB")
    img = Image.new("RGB", (gifWidth * pixelWidth, gifHeight * pixelHeight))
    for y in range(gifHeight):
        for x in range(gifWidth):
            img.paste(pixel0, (x * pixelWidth, y * pixelHeight))

    # Calculate the starting x position to center the video frame
    baStartX = (gifWidth - scaledFrameWidth // scale) // 2


    for gifFrameY in range(gifHeight):
        for gifFrameX in range(gifWidth):
            frameY = gifFrameY * scale
            frameX = (gifFrameX - baStartX) * scale

            if frameX >= 0 and frameX < scaledFrameWidth and frameY >= 0 and frameY < scaledFrameHeight:
                frameQuad = frame[frameY:frameY+2, frameX:frameX+2]
                intensities = getIntensities(frameQuad)

                pixelIntensity = np.mean(intensities)
                # if the framePixel is brighter than the initialPixel or it has aloready been replaced, then use the framePixel
                if pixelIntensity >= initialPixels[gifFrameY, gifFrameX] or pixelReplaced[gifFrameY, gifFrameX]:
                    pixelReplaced[gifFrameY, gifFrameX] = 1 
                                       
                elif not pixelReplaced[gifFrameY, gifFrameX]:
                    # else, then use the initialPixel
                    intensities = [initialPixels[gifFrameY, gifFrameX]]*4
                    
            elif not pixelReplaced[gifFrameY, gifFrameX]:
                # If the pixel is outside the video frame, use initialPixels
                    intensities = [initialPixels[gifFrameY, gifFrameX]]*4


            pixelImg = getSubPixels(intensities)
            pixelImg = Image.fromarray(pixelImg)
            pastePos = (gifFrameX * pixelWidth, gifFrameY * pixelHeight)
            img.paste(pixelImg, pastePos)
    
    
    imgFrames.append(img)
    print(f"Processed GIF frame {i + 1}/{len(frames)}          ", end="\r")

print("Processed GIF Done             \n")

print("Saving GIF...", end="\r")

# calculate the duration of the gif using the video frame rate, and the number of frames skipped
duration = 1000 / (videoFps / frameSkip)  # 1 second / (frames per second / frameSkip)

imgFrames[0].save(
    outputGif, save_all=True, append_images=imgFrames[1:], loop=0, duration=duration
)

print(f"Saving GIF Done - {outputGif}")