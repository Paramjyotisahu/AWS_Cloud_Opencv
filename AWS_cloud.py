import webbrowser
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import boto3
import os
import qrcode
import cv2
import mediapipe as mp
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from math import hypot

def Volume_by_hand_gesture():

    # solution APIs
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands

    # Volume Control Library Usage 
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol , maxVol , volBar, volPer= volRange[0] , volRange[1], 400, 0

    # Webcam Setup
    wCam, hCam = 640, 480
    cam = cv2.VideoCapture(0)
    cam.set(3,wCam)
    cam.set(4,hCam)

    # Mediapipe Hand Landmark Model
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:

      while cam.isOpened():
        success, image = cam.read()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if results.multi_hand_landmarks:
          for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
                )

        # multi_hand_landmarks method for Finding postion of Hand landmarks      
        lmList = []
        if results.multi_hand_landmarks:
          myHand = results.multi_hand_landmarks[0]
          for id, lm in enumerate(myHand.landmark):
            h, w, c = image.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            lmList.append([id, cx, cy])          

        # Assigning variables for Thumb and Index finger position
        if len(lmList) != 0:
          x1, y1 = lmList[4][1], lmList[4][2]
          x2, y2 = lmList[8][1], lmList[8][2]

          # Marking Thumb and Index finger
          cv2.circle(image, (x1,y1),15,(255,255,255))  
          cv2.circle(image, (x2,y2),15,(255,255,255))   
          cv2.line(image,(x1,y1),(x2,y2),(0,255,0),3)
          length = math.hypot(x2-x1,y2-y1)
          if length < 50:
            cv2.line(image,(x1,y1),(x2,y2),(0,0,255),3)

          vol = np.interp(length, [50, 220], [minVol, maxVol])
          volume.SetMasterVolumeLevel(vol, None)
          volBar = np.interp(length, [50, 220], [400, 150])
          volPer = np.interp(length, [50, 220], [0, 100])

          # Volume Bar
          cv2.rectangle(image, (50, 150), (85, 400), (0, 0, 0), 3)
          cv2.rectangle(image, (50, int(volBar)), (85, 400), (0, 0, 0), cv2.FILLED)
          cv2.putText(image, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                    1, (0, 0, 0), 3)

        cv2.imshow('handDetector', image) 
        if cv2.waitKey(1) & 0xFF == ord('q'):
          break
    cam.release()


def generate_qr_code():
    data = simpledialog.askstring("QR Code Generator", "Enter the text or URL to encode:")
    if data:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save("qr_code.png")
        img.show()

def open_youtube():
    song_name = simpledialog.askstring("Open YouTube", "Enter the name of your favorite song:")
    if song_name:
        search_query = song_name.replace(" ", "+")
        webbrowser.open(f"https://www.youtube.com/results?search_query={search_query}")

def google_search():
    search_query = simpledialog.askstring("Google Search", "Enter your search query:")
    if search_query:
        webbrowser.open(f"https://www.google.com/search?q={search_query}")

def list_ec2_instances():
    try:
        ec2 = boto3.client("ec2")
        response = ec2.describe_instances()
        instances = response["Reservations"]

        if not instances:
            messagebox.showinfo("No EC2 Instances", "No EC2 instances found.")
        else:
            instance_info = "\n".join([f"ID: {instance['Instances'][0]['InstanceId']}, "
                                       f"State: {instance['Instances'][0]['State']['Name']}"
                                       for instance in instances])
            messagebox.showinfo("EC2 Instances", f"List of EC2 instances:\n{instance_info}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to list EC2 instances: {e}")

def open_ec2_instance():
    response = messagebox.askyesno("AWS EC2 Instance", "Do you want to create an EC2 instance?")
    if response:
        myec2 = boto3.client("ec2")
        response = myec2.run_instances(  
            ImageId='ami-0da59f1af71ea4ad2', 
            InstanceType='t2.micro',
            MaxCount=1,
            MinCount=1
        )
        print(response)

def create_s3_bucket():
    response = messagebox.askyesno("AWS S3 Bucket", "Do you want to create an S3 bucket?")
    if response:
        s3 = boto3.client('s3')
        s3 = s3.create_bucket(
            Bucket='name',
            ACL='private',
            CreateBucketConfiguration={
                'LocationConstraint': 'ap-south-1'
            }
        )
        print("Bucket created successfully with the following response:")
        print(s3)
        print("Bucket 'new' was created in the 'ap-south-1' region.")

def upload_to_s3():
    bucket_name = simpledialog.askstring("Upload to S3 Bucket", "Enter the bucket name:")
    if bucket_name:
        file_path = filedialog.askopenfilename(title="Select a file to upload")
        if file_path:
            try:
                s3 = boto3.client("s3")
                file_name = os.path.basename(file_path)
                s3.upload_file(file_path, bucket_name, file_name)
                messagebox.showinfo("Upload Successful", f"File '{file_name}' uploaded to '{bucket_name}'")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload file: {e}")

def capture_video():
    if messagebox.askyesno("Exit", "Want to Capture ?"):
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter("captured_video.avi", fourcc, 20.0, (640, 480))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        messagebox.showinfo("Video Captured", "Video captured and saved as 'captured_video.avi'")

# Create Tkinter window
root = tk.Tk()
root.title("AWS Management")

# Set window size and background color
root.geometry("1200x750")
root.configure(bg="black")

# Create a frame for buttons
button_frame = tk.Frame(root, bg="black")
button_frame.pack(pady=10)

# Configure button font
button_font = ("Arial", 12, "italic")

# Create buttons for each function
btn_list_instances = tk.Button(button_frame, text="List EC2 Instances", command=list_ec2_instances, font=button_font, width=20, height=2)
btn_list_instances.grid(row=0, column=0, padx=10, pady=5)

btn_create_instance = tk.Button(button_frame, text="Create EC2 Instance", command=open_ec2_instance, font=button_font, width=20, height=2)
btn_create_instance.grid(row=0, column=1, padx=10, pady=5)

btn_create_bucket = tk.Button(button_frame, text="Create S3 Bucket", command=create_s3_bucket, font=button_font, width=20, height=2)
btn_create_bucket.grid(row=1, column=0, padx=10, pady=5)

btn_upload_to_s3 = tk.Button(button_frame, text="Upload to S3", command=upload_to_s3, font=button_font, width=20, height=2)
btn_upload_to_s3.grid(row=1, column=1, padx=10, pady=5)

btn_volume_control = tk.Button(button_frame, text="Volume Control", command=Volume_by_hand_gesture, font=button_font, width=20, height=2)
btn_volume_control.grid(row=1, column=2, padx=10, pady=5)

btn_generate_qr_code = tk.Button(button_frame, text="Generate QR Code", command=generate_qr_code, font=button_font, width=20, height=2)
btn_generate_qr_code.grid(row=2, column=0, padx=10, pady=5)
                             
btn_open_youtube = tk.Button(button_frame, text="Open YouTube", command=open_youtube, font=button_font, width=20, height=2)
btn_open_youtube.grid(row=3, column=1, padx=10, pady=5)

btn_google_search = tk.Button(button_frame, text="Google Search", command=google_search, font=button_font, width=20, height=2)
btn_google_search.grid(row=4, column=0, padx=10, pady=5)

btn_capture_video = tk.Button(button_frame, text="Capture Video", command=capture_video, font=button_font, width=20, height=2)
btn_capture_video.grid(row=4, column=1, padx=10, pady=5)

root.mainloop()
