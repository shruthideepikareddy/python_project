import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
from cvzone.FaceMeshModule import FaceMeshDetector
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
import turtle
from tkinter import Canvas

# Load environment variables
load_dotenv()

# UI Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AttendanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Attendance Dashboard")
        self.geometry("1440x900")

        # Initialize Data & Engines
        self.setup_engines()
        self.setup_ui()
        
        # Camera Loop
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)
        
        self.update_frame()

    def setup_engines(self):
        # Supabase
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            print("Credentials missing!")
            exit()
        self.supabase = create_client(self.url, self.key)
        
        # Face Recognition
        print("Loading Encodings...")
        with open('EncodeFile.p', 'rb') as f:
            self.encodeListKnown, self.studentIds = pickle.load(f)
        
        # Liveness
        self.detector = FaceMeshDetector(maxFaces=1)
        self.blinkCounter = 0
        self.liveness_verified = False
        
        # App State
        self.attendance_counter = 0
        self.current_student = None
        self.last_recognition_time = 0
        self.is_processing = False

    def setup_ui(self):
        # Grid layout 1x2 (Sidebar and Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 🟢 SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="TRUSTY HANDS", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))
        
        self.sub_label = ctk.CTkLabel(self.sidebar, text="Smart Attendance System", font=ctk.CTkFont(size=14))
        self.sub_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Student Photo Box
        self.photo_frame = ctk.CTkFrame(self.sidebar, width=200, height=200, corner_radius=100)
        self.photo_frame.grid(row=2, column=0, padx=20, pady=20)
        self.photo_label = ctk.CTkLabel(self.photo_frame, text="No Face Detected", text_color="gray")
        self.photo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Student Info Card
        self.info_frame = ctk.CTkFrame(self.sidebar, corner_radius=15, fg_color="transparent")
        self.info_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        self.name_val = ctk.CTkLabel(self.info_frame, text="---", font=ctk.CTkFont(size=22, weight="bold"))
        self.name_val.pack(pady=(10, 5))
        
        self.id_val = ctk.CTkLabel(self.info_frame, text="ID: ---", font=ctk.CTkFont(size=14))
        self.id_val.pack()
        
        self.major_val = ctk.CTkLabel(self.info_frame, text="Major: ---", font=ctk.CTkFont(size=14))
        self.major_val.pack()

        self.attendance_val = ctk.CTkLabel(self.sidebar, text="0", font=ctk.CTkFont(size=48, weight="bold"), text_color="#1f538d")
        self.attendance_val.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="s")

        # Turtle Canvas for Scanning Animation
        self.canvas = Canvas(self.sidebar, width=200, height=50, bg='#2b2b2b', highlightthickness=0)
        self.canvas.grid(row=6, column=0, pady=(0, 20))
        self.setup_turtle()

        # 🔵 MAIN VIEW
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_view.grid_rowconfigure(0, weight=1)
        self.main_view.grid_columnconfigure(0, weight=1)

        # Camera Feed
        self.camera_label = ctk.CTkLabel(self.main_view, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Control Bar
        self.controls = ctk.CTkFrame(self.main_view, height=80, corner_radius=15)
        self.controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.report_btn = ctk.CTkButton(self.controls, text="Generate Daily Report", command=self.trigger_report, fg_color="#2ecc71", hover_color="#27ae60")
        self.report_btn.pack(side="left", padx=20, pady=20)
        
        self.status_label = ctk.CTkLabel(self.controls, text="SYSTEM READY", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498db")
        self.status_label.pack(side="right", padx=20)

    def setup_turtle(self):
        self.screen = turtle.TurtleScreen(self.canvas)
        self.screen.bgcolor("#2b2b2b")
        self.t = turtle.RawTurtle(self.screen)
        self.t.hideturtle()
        self.t.speed(0)
        self.t.color("#3498db")
        self.t.width(3)
        self.scanning = True
        self.animate_turtle()

    def animate_turtle(self):
        if not hasattr(self, 't'): return
        self.t.clear()
        if self.liveness_verified:
            # Draw a checkmark
            self.t.color("#2ecc71")
            self.t.penup()
            self.t.goto(-20, 0)
            self.t.pendown()
            self.t.goto(-5, -15)
            self.t.goto(20, 15)
        else:
            # Scanning bar
            self.t.color("#3498db")
            y = (int(time.time() * 50) % 40) - 20
            self.t.penup()
            self.t.goto(-50, y)
            self.t.pendown()
            self.t.goto(50, y)
        
        if self.winfo_exists():
            self.after(50, self.animate_turtle)

    def trigger_report(self):
        self.status_label.configure(text="SENDING REPORT...", text_color="#f1c40f")
        threading.Thread(target=self._send_report_thread, daemon=True).start()

    def _send_report_thread(self):
        try:
            from report_sender import generate_excel_report, send_email_with_attachment
            filename = generate_excel_report()
            send_email_with_attachment(filename)
            os.remove(filename)
            self.after(0, lambda: self.status_label.configure(text="REPORT SENT!", text_color="#2ecc71"))
        except Exception as e:
            print(f"Report Error: {e}")
            self.after(0, lambda: self.status_label.configure(text="REPORT FAILED", text_color="#e74c3c"))

    def update_frame(self):
        success, img = self.cap.read()
        if not success:
            self.after(10, self.update_frame)
            return

        # 1. Processing for Liveness & Recognition
        processed_img, info = self.process_logic(img)

        # 2. Convert to PhotoImage for CustomTkinter
        img_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        
        # Maintain aspect ratio for the dashboard
        w, h = self.camera_label.winfo_width(), self.camera_label.winfo_height()
        if w > 10 and h > 10:
            img_pil = img_pil.resize((w, h), Image.Resampling.LANCZOS)
        
        img_tk = ImageTk.PhotoImage(img_pil)
        self.camera_label.configure(image=img_tk)
        self.camera_label._image_tk = img_tk  # Keep reference

        self.after(10, self.update_frame)

    def process_logic(self, img):
        # Liveness Detection
        img, faces = self.detector.findFaceMesh(img, draw=False)
        if faces:
            face = faces[0]
            leftEye = [face[145], face[159]]
            rightEye = [face[374], face[386]]
            leftDist, _ = self.detector.findDistance(leftEye[0], leftEye[1])
            rightDist, _ = self.detector.findDistance(rightEye[0], rightEye[1])
            
            if leftDist < 25 and rightDist < 25:
                self.blinkCounter += 1
                self.status_label.configure(text="BLINK DETECTED - VERIFIED", text_color="#2ecc71")
            
            if self.blinkCounter > 0:
                self.liveness_verified = True

        # Recognition Logic
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        
        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(self.encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(self.encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    reg_num = self.studentIds[matchIndex]
                    y1, x2, y2, x1 = [v * 4 for v in faceLoc]
                    
                    # Draw UI on frame
                    color = (0, 255, 0) if self.liveness_verified else (0, 255, 255)
                    cvzone.cornerRect(img, (x1, y1, x2-x1, y2-y1), colorC=color, rt=2)
                    
                    if not self.liveness_verified:
                        cv2.putText(img, "BLINK TO VERIFY", (x1, y1-10), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)
                    else:
                        if not self.is_processing and (time.time() - self.last_recognition_time > 10):
                            self.trigger_attendance(reg_num)

        else:
            # Reset state if no face
            if not self.is_processing:
                self.liveness_verified = False
                self.blinkCounter = 0
                self.status_label.configure(text="SCANNING...", text_color="#3498db")

        return img, None

    def trigger_attendance(self, reg_num):
        self.is_processing = True
        self.last_recognition_time = time.time()
        self.status_label.configure(text="UPDATING ATTENDANCE...", text_color="#f1c40f")
        threading.Thread(target=self._db_thread, args=(reg_num,), daemon=True).start()

    def _db_thread(self, reg_num):
        try:
            # Fetch Info
            res = self.supabase.table("students").select("*").eq("registration_number", reg_num).execute()
            if res.data:
                student = res.data[0]
                
                # Check Time
                last_time = datetime.strptime(student['last_attendance_time'], "%Y-%m-%dT%H:%M:%S")
                if (datetime.now() - last_time).total_seconds() > 30:
                    new_total = student['total_attendance'] + 1
                    self.supabase.table('students').update({
                        'total_attendance': new_total,
                        'last_attendance_time': datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    }).eq('registration_number', reg_num).execute()
                    student['total_attendance'] = new_total
                
                # Fetch Image
                bucket = self.supabase.storage.from_("images")
                file_content = bucket.download(f"{reg_num}.png")
                array = np.frombuffer(file_content, np.uint8)
                img_cv = cv2.imdecode(array, cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb).resize((200, 200))
                photo = ImageTk.PhotoImage(img_pil)

                # Update UI
                self.after(0, lambda: self.update_student_ui(student, photo))
        except Exception as e:
            print(f"DB Error: {e}")
        finally:
            self.is_processing = False

    def update_student_ui(self, data, photo):
        self.name_val.configure(text=data['name'])
        self.id_val.configure(text=f"ID: {data['registration_number']}")
        self.major_val.configure(text=f"Major: {data['major']}")
        self.attendance_val.configure(text=str(data['total_attendance']))
        self.photo_label.configure(image=photo, text="")
        self.photo_label.image = photo
        self.status_label.configure(text="ATTENDANCE MARKED", text_color="#2ecc71")

if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()
