import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
from supabase import create_client, Client
import offset
from datetime import datetime
# Supabase credentials
SUPABASE_URL = "https://hlhzjdzqfwrmoultblat.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaHpqZHpxZndybW91bHRibGF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI0MDgxNjMsImV4cCI6MjA1Nzk4NDE2M30.xWHJh_llH7MNf-g0Dic9EXvXjzSBMSGuYc0VX0uuAEM"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
imgBackground = cv2.imread('resources/background.png')
# Importing mode images into a list
folderModePath = 'resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
# Load the encoding file
print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")
modeType = 0
counter = 0
registration_number = None
imgStudent=[]
while True:
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    
    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            
        if matches[matchIndex]:
        # your existing logic
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = (55 + x1, 162 + y1, x2 - x1, y2 - y1)

                    # 🟢 **React-style real-time tracking box**
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, colorC=(0, 255, 0), colorR=(255, 0, 0), rt=2)

                    registration_number = studentIds[matchIndex]

                    if counter == 0:
                        cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                        cv2.imshow("Face Attendance", imgBackground)
                        cv2.waitKey(1)
                        counter = 1
                        modeType = 1

        if counter != 0:
            if counter == 1:
                # Fetch student info from Supabase (assuming Supabase database table is used)
                data = supabase.table("students").select("*").eq("registration_number", registration_number).execute()
                if data.data:
                    studentInfo = data.data[0]
                #get the image from the storage
                image_id = registration_number  # Replace with your image ID
                bucket = supabase.storage.from_("images")

                # Fetch the file content from the storage bucket using the download method
                try:
                    file_content = bucket.download(f"{image_id}.png")
                    array = np.frombuffer(file_content, np.uint8)
                    img_student = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    # Check if the image is successfully decoded
                except Exception as e:
                    print(f"An error occurred: {e}")
                # Update data of attendance
                datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%dT%H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)

                if secondsElapsed > 30:
                    student_data = supabase.table('students').select('*').eq('registration_number', registration_number).single().execute().data
                    studentInfo['total_attendance'] += 1
                    supabase.table('students').update({'total_attendance': studentInfo['total_attendance']}).eq('registration_number', studentInfo['registration_number']).execute()
                    supabase.table('students').update({'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).eq('registration_number', studentInfo['registration_number']).execute()
                else:
                    modeType = 3
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
            if modeType!=3:
                # Put text on image
                if 10 < counter < 20:
                    modeType = 2

                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if counter <= 10:
                    cv2.putText(imgBackground, str(studentInfo['total_attendance']),(861,125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['major']),(1006,550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['registration_number']),(1000,493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(studentInfo['standing']),(910,625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(studentInfo['year']),(1025,625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(studentInfo['starting_year']),(1125,625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    
                    (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(studentInfo['name']),(808+offset,445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
                
                

                    imgBackground[175:175 + 216, 909:909 + 216] = img_student
                 

            counter+=1
            if counter >= 20:
                counter = 0
                modeType = 0
                studentInfo = []
                imgStudent = []
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    
    else:
        modeType = 0
        counter = 0
    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)
