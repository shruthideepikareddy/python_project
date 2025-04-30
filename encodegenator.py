import cv2
import face_recognition
import pickle
import os
import requests

# Supabase credentials (replace with your actual values)
SUPABASE_URL = "https://hlhzjdzqfwrmoultblat.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaHpqZHpxZndybW91bHRibGF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI0MDgxNjMsImV4cCI6MjA1Nzk4NDE2M30.xWHJh_llH7MNf-g0Dic9EXvXjzSBMSGuYc0VX0uuAEM"  # Use your service_role key
  # Ensure this matches your bucket name

# Importing student images
folderPath = 'photos'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
studentIds = []

for path in pathList:
    img_path = os.path.join(folderPath, path)
    imgList.append(cv2.imread(img_path))
    studentIds.append(os.path.splitext(path)[0])

    

print(studentIds)

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("Encoding Complete")

with open("EncodeFile.p", 'wb') as file:
    pickle.dump(encodeListKnownWithIds, file)
print("File Saved")
