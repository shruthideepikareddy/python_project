import cv2
import face_recognition
import pickle
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")

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
