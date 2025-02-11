import cv2
import numpy as np
from PIL import Image


# Parameters
VIDEOPATH = "Bad Apple.mp4"  # Path to the input video
OUTPUTGIF = "Bad Apple.gif"  # Name of the generated GIF

GIFHEIGHT = 7  # commit pixel
GIFWIDTH = 52  # commit pixel
FRAME_SKIP = 1 # Frame skip multiplier (min 1)

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

USESUBPIXELS = True

# Load the video
print(f"Loading Video `{VIDEOPATH}`...", end=" ")
cap = cv2.VideoCapture(VIDEOPATH)
frames = []
frameCount = 0
print("Done")

videoLenght = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
videoFps = cap.get(cv2.CAP_PROP_FPS)
videoTime = videoLenght / videoFps

print(f"""
Video Info:
  - Frame Count: {videoLenght}
  - Frame Rate: {videoFps}fps
  - Frame Time: {1/videoFps}s
  - Video Time: {videoTime}s
""")

targetDuration = 40
FRAMESKIP = targetDuration * (videoFps / 1000)
targetDuration = round(targetDuration*FRAME_SKIP, 5)
FRAMESKIP = round(FRAMESKIP*FRAME_SKIP, 5)# multiplied by itself so that you can set a frameSkip manually, but the correct one will be calculated(default 1 -> no skip)
if FRAMESKIP < 1:
    print("Warning: Frame Skip is less than 1, setting it to 1")
    FRAMESKIP = 1

print(f"""Frame Skip: {FRAME_SKIP}
Calculated Frame Time: {targetDuration}ms
Calculated Frame Skip: {FRAMESKIP}
""")

print("Processing Video...", end="\r")
accumulator = 0.0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to grayscale & resize while maintaining aspect ratio
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    aspectRatio = frame.shape[1] / frame.shape[0]
    scale = 2
    scaledFrameWidth = int(GIFHEIGHT * aspectRatio) * scale
    scaledFrameHeight = GIFHEIGHT * scale

    # Normalize pixels
    normalizedFrame = np.clip(frame / 255 * (pixelNum - 1), 0, pixelNum - 1)
    normalizedResizedFrame = cv2.resize(
        normalizedFrame, (scaledFrameWidth, scaledFrameHeight), interpolation=cv2.INTER_AREA
    )

    frameCount += 1
    accumulator += 1
    if accumulator >= FRAMESKIP:
        accumulator -= FRAMESKIP
        frames.append(normalizedResizedFrame)

    print(f"Processed Video frame {frameCount}/{videoLenght}          ", end="\r")

cap.release()

print("Processing Video Done             ")


print(f"""
GIF Info:
  - Frame Count: {len(frames)}
  - Frame Rate: {1000 / targetDuration}fps
  - Frame Time: {targetDuration/1000}s
  - Total Time: {len(frames) * targetDuration / 1000}s
""")


def getIntensities(frameQuad):
    intensities = []
    for y in range(2):
        for x in range(2):
            intensity = round(frameQuad[y, x])
            intensities.append(intensity)
    
    return intensities

pixelmate = np.zeros((pixelHeight, pixelWidth, 3), dtype=np.uint8)
def getSubPixels(intensities: list):
    

    # if USESUBPIXELS is set to false, then all intensities are set to the mean value
    if not USESUBPIXELS:
        intensities = [int(np.mean(intensities))]*4
    
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
initialPixels = np.clip(np.random.normal(0, 1.5, (GIFHEIGHT, GIFWIDTH)), 0, pixelNum-1).astype(int)

# Initialize pixelReplaced array
pixelReplaced = np.zeros((GIFHEIGHT, GIFWIDTH), dtype=int)

# Create the GIF
imgFrames = []
for i, frame in enumerate(frames):
    # Create a new image filled with pixel0
    pixel0 = githubPixels[0].convert("RGB")
    img = Image.new("RGB", (GIFWIDTH * pixelWidth, GIFHEIGHT * pixelHeight))
    for y in range(GIFHEIGHT):
        for x in range(GIFWIDTH):
            img.paste(pixel0, (x * pixelWidth, y * pixelHeight))

    # Calculate the starting x position to center the video frame
    baStartX = (GIFWIDTH - scaledFrameWidth // scale) // 2


    for gifFrameY in range(GIFHEIGHT):
        for gifFrameX in range(GIFWIDTH):
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


# Number of fade frames for a single pixel
fadeFramesCount = 20

# Create a random start frame for each pixel's fade-in
fadeStartFrames = np.random.randint(0, fadeFramesCount, (GIFHEIGHT, GIFWIDTH))

# Create fade frames
for fadeFrameIndex in range(1, fadeFramesCount + 10):
    fadeImg = Image.new("RGB", (GIFWIDTH * pixelWidth, GIFHEIGHT * pixelHeight))
    for y in range(GIFHEIGHT):
        for x in range(GIFWIDTH):
            pixel0 = githubPixels[0].convert("RGB")
            finalPixel = imgFrames[-1].crop((x * pixelWidth, y * pixelHeight, (x + 1) * pixelWidth, (y + 1) * pixelHeight))
            initialPixel = githubPixels[initialPixels[y, x]].convert("RGB")
            
            # Calculate the fade factor based on the pixel's start frame
            if fadeFrameIndex >= fadeStartFrames[y, x]:
                fadeFactor = (fadeFrameIndex - fadeStartFrames[y, x]) / fadeFramesCount
                fadeFactor = min(fadeFactor, 1)  # Ensure fadeFactor does not exceed 1
            else:
                fadeFactor = 0
            
            blendedPixel = Image.blend(finalPixel, initialPixel, fadeFactor)
            fadeImg.paste(blendedPixel, (x * pixelWidth, y * pixelHeight))
    imgFrames.append(fadeImg)
    print(f"Processed Fade frame {fadeFrameIndex}/{fadeFramesCount}          ", end="\r")

print("Processed Fade Frames Done             \n")


print(f"""
Frame duration: {targetDuration}ms
Total frames: {len(imgFrames)}
Total time: {len(imgFrames) * targetDuration / 1000}s (higher than the video time due to fade frames)

Saving GIF as `{OUTPUTGIF}`...""", end=" ")
# don't asky why it's here, if it's it's own print it doesn't print before the gif is saved

imgFrames[0].save(
    OUTPUTGIF, save_all=True, append_images=imgFrames[1:], loop=0, duration=targetDuration
)

print(f"Done\n")