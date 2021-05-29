import cv2
import numpy as np
import autopy
import time
import HandTrackingModule as htm

#For Volume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0

#Frame
wCam, hCam = 640, 480
wScr, hScr = autopy.screen.size()
frameR = 110
smoothening = 5

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(maxHands=1)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmlist, bbox = detector.findPos(img)

    #Tip of index and middle finger
    if len(lmlist) != 0:
        x1, y1 = lmlist[8][1:]
        x2, y2 = lmlist[12][1:]

        #Check which fingers up
        fingers = detector.fingersUp()
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR - 15), (255, 0, 255), 2)  # Eligible Frame for movement
        if fingers[1] == 1 and fingers[0] == 0 and fingers[2:] == [0, 0, 0]:
            x3 = np.interp(x1, (frameR, wCam-frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam-frameR - 15), (0, hScr))

            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            autopy.mouse.move(clocX,clocY) #Move Mouse
            cv2.circle(img, (x1,y1), 9, (255,0,255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        if fingers[1] == 1 and fingers[2] == 1:
            length, img, info = detector.findDistance(8, 12, img)
            if length < 30: #If distance less than threshold
                autopy.mouse.click() #Click
                cv2.circle(img, (info[4], info[5]), 9, (255, 0, 0), cv2.FILLED)
        
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2:4] == [0, 0] and fingers[4] == 1:
            length, img, _ = detector.findDistance(4, 8, img)
            vol = np.interp(length, [30, 120], [minVol, maxVol])
            volBar = np.interp(length, [30, 120], [400, 150])
            volPer = np.interp(length, [30, 120], [0, 100])
            # print(int(length), vol)
            volume.SetMasterVolumeLevel(vol, None)

            cv2.rectangle(img, (30, 150), (40, 400), (255, 0, 0), 3)
            cv2.rectangle(img, (30, int(volBar)), (40, 400), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, f'{int(volPer)} %', (18, 425), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
    #FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (10, 70,), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)

    cv2.imshow('Image', img)
    cv2.waitKey(1)
