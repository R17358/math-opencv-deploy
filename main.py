#https://ai.google.dev/gemini-api/docs/quickstart?lang=python
#https://aistudio.google.com/app/apikey
#pip install -q -U google-generativeai

#python - m streamlit run main.py
import cvzone   
import cv2
from cvzone.HandTrackingModule import HandDetector    
import numpy as np
import google.generativeai as genai
import os
from PIL import Image
import streamlit as st
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

st.set_page_config(layout="wide")
#st.image()
#st.columns(2)   # equal 2 splits
col1, col2 = st.columns([2,1]) # 2:1 split

with col1:
    run = st.checkbox('Run', value=False)
    if run:
        FRAME_WINDOW = st.image([])
    else:
        FRAME_WINDOW = None

with col2:
    output_text_area = st.title("Answer")
    output_text_area = st.subheader("")


genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize the webcam to capture video
# The '2' indicates the third camera connected to your computer; '0' would usually refer to the built-in camera
cap = cv2.VideoCapture(0)
cap.set(3, 980)
cap.set(4, 620)

# Initialize the HandDetector class with the given parameters
detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=1, detectionCon=0.5, minTrackCon=0.5)


def getHandInfo(img):
    # Find hands in the current frame
    # The 'draw' parameter draws landmarks and hand outlines on the image if set to True
    # The 'flipType' parameter flips the image, making it easier for some detections
    hands, img = detector.findHands(img, draw=True, flipType=True)

    # Check if any hands are detected
    if hands:
        # Information for the first hand detected
        hand = hands[0]  # Get the first hand detected
        lmList = hand["lmList"]  # List of 21 landmarks for the first hand

        # Count the number of fingers up for the first hand
        fingers = detector.fingersUp(hand)
        return fingers, lmList
        # print(f'H1 = {fingers1.count(1)}', end=" ")  # Print the count of fingers that are up
        # # Calculate distance between specific landmarks on the first hand and draw it on the image
        # length, info, img = detector.findDistance(lmList1[8][0:2], lmList1[12][0:2], img, color=(255, 0, 255),
        #                                             scale=10)
    else:
        return None

def draw(info, prev_pos, canvas):
    fingers, lmList = info
    current_pos = None

    if fingers == [0,1,0,0,0]: # index finger is Up
        current_pos = lmList[8][0:2]    # landmark of index tip is 8 and x, y [0:2] i.e 0,1
        if prev_pos == None:            # at Start
            prev_pos = current_pos
        cv2.line(canvas, current_pos, prev_pos, (255, 0, 255), 10)
    
    elif fingers == [0,0,0,0,1]:
        canvas = np.zeros_like(img)
    
    return current_pos, canvas

def sendToAI(model, canvas, fingers):
    if fingers == [0,1,1,1,1]:
        pil_image = Image.fromarray(canvas)
        response = model.generate_content(["Solve this math problem", pil_image])
        #print(response.text)
        return response.text


def format_text(text):
    ans = ""
    words = text.split()
    i = 1
    for word in words:  
        if i%6==0:
            ans = ans + "\n"
        else:
            ans = ans + word + " "
        i = i+1
    return ans


prev_pos = None
canvas = None
image_combine = None
output_text = ""

# Continuously get frames from the webcam
while run:
    # Capture each frame from the webcam
    # 'success' will be True if the frame is successfully captured, 'img' will contain the frame
    success, img = cap.read()
    img = cv2.flip(img, 1)  #flip code is 1 means horizonatally flip

    if canvas is None:
        canvas = np.zeros_like(img)

    info = getHandInfo(img)

    if info:
        fingers, lmList = info
        #print(fingers) 
        prev_pos, canvas = draw(info, prev_pos, canvas)
        output_text = sendToAI(model, canvas, fingers)

    image_combine = cv2.addWeighted(img, 0.6, canvas, 0.4, 0)
    if FRAME_WINDOW:
        FRAME_WINDOW.image(image_combine, channels="BGR")

    if output_text:
        formatted_text = format_text(output_text)
        output_text_area.text(formatted_text)
        time.sleep(1)
    # Display the image in a window
    #cv2.imshow("Image", img)
    # cv2.imshow("Canvas", canvas)
    # cv2.imshow("imageCombined", image_combine)
    #final_img = cvzone.stackImages([image_combine,canvas], 2, 0.5)
    #cv2.imshow("final Image", final_img)
    # Keep the window open and update it for each frame; wait for 1 millisecond between frames
    cv2.waitKey(1)
