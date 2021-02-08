import numpy as np 
import cv2 
import imutils
  
cap = cv2.VideoCapture(0)   
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D') 
out = cv2.VideoWriter('output.avi', fourcc, 20, (frame_width, frame_height)) 

while(True): 
    ret, frame = cap.read()
    #frame = imutils.resize(frame, width=300)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('frame', gray)
    out.write(gray)
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break
  
print("Done capturing!")
cap.release() 
out.release()  
cv2.destroyAllWindows() 
