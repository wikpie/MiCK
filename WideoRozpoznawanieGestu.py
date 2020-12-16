# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 16:59:05 2020

@author: emilk, wiktorP
"""

import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
from PIL import ImageTk, Image
import time
from tkinter import filedialog
import os
import numpy as np
import math
import presentation


class App:
    left_finger = 0

    def __init__(self, window, window_title, video_source=0):

        self.window = window
        self.window.title(window_title)
        self.video_source = video_source

        self.vid = MyVideoCapture(self.video_source)
        # Panel tekstowy boczny
        self.t = tk.Text(root, bg="#5e2f45", width=25, fg="#ffffff", yscrollcommand=yscrollbar.set)
        self.t.insert(tk.INSERT, "Wynik")
        yscrollbar.config(command=self.t.yview)
        self.t.pack(side="right", fill=tk.Y)

        # Okna wideo
        self.canvas = tk.Canvas(window, width=650, height=400)
        self.canvas.place(x=160)

        self.canvas2 = tk.Canvas(root, width=650, height=400)
        self.canvas2.place(x=160, y=400)

        self.canvas3 = tk.Canvas(root, width=250, height=250)
        self.canvas3.place(x=800)

        # Przycisk zrzutu ekranu
        self.btn_snapshot = tk.Button(window, text="Snapshot", width=20, bg="#ad527b", fg="#ffffff",
                                      command=self.snapshot)
        self.btn_snapshot.place(x=5, y=35)

        # Częstotliwoć aktualizacji klatki filmy na ekranie
        self.delay = 500
        self.update()

        self.window.mainloop()

    def snapshot(self):

        ret, frame = self.vid.get_frame()
        frame = cv2.flip(frame, 1)
        cv2.rectangle(frame, (400, 150), (640, 400), (255, 0, 0), 2)
        kernel = np.ones((3, 3), np.uint8)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 60], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.dilate(mask, kernel, iterations=1)
        mask = cv2.GaussianBlur(mask, (3, 3), 100)

        # opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        cv2.rectangle(closing, (400, 150), (650, 400), (255, 0, 0), 2)
        blur1 = cv2.GaussianBlur(closing, (5, 5), 0)
        ret, closing = cv2.threshold(blur1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite('1_w.png', closing)
        roi = closing[150:400, 400:650]
        blur = cv2.GaussianBlur(roi, (5, 5), 0)
        ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite('o.png', th3)

        if ret:
            cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", frame)

    def update(self):
        # Wycinam tylko obszar ręki
        wynik = ""
        ret, frame = self.vid.get_frame()
        frame = cv2.flip(frame, 1)
        kernel = np.ones((3, 3), np.uint8)

        # wybranie ROI
        roi = frame[100:300, 100:300]

        cv2.rectangle(frame, (100, 100), (300, 300), (0, 255, 0), 0)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # zdefiniowanie zakresu HSV koloru skóry
        lower_skin = np.array([0, 20, 60], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower_skin, upper_skin)

        mask = cv2.dilate(mask, kernel, iterations=4)

        mask = cv2.GaussianBlur(mask, (5, 5), 100)

        # Wyszukiwanie konturów
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Wyszukiwanie konturu dłoni, czyli max kontur w tym przypadku
        cnt = max(contours, key=lambda x: cv2.contourArea(x))

        # Aproksymacja
        epsilon = 0.0005 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # zdefiniowanie obramowania reki
        hull = cv2.convexHull(cnt)

        # obszar wokół ręki i obszar ręki
        areahull = cv2.contourArea(hull)
        hand_area = cv2.contourArea(cnt)

        # Procentowa część obszaru hull, nie zajmowana przez kontur dłoni
        handless_area = ((areahull - hand_area) / hand_area) * 100

        # Wyszukiwanie defektów
        hull = cv2.convexHull(approx, returnPoints=False)
        defects = cv2.convexityDefects(approx, hull)

        # fingers = liczba znalezionych palców
        fingers = 0

        # znadjywanie palców
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(approx[s][0])
            end = tuple(approx[e][0])
            far = tuple(approx[f][0])
            pt = (100, 180)

            a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
            b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
            c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
            s = (a + b + c) / 2
            ar = math.sqrt(s * (s - a) * (s - b) * (s - c))

            d = (2 * ar) / a

            angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 57

            if angle <= 90 and d > 30:
                fingers += 1
                print(str(angle) + " " + str(d) + " " + str(a) + " " + str(b) + " " + str(c))
                cv2.circle(roi, far, 3, [255, 0, 0], -1)
                # do gestów w prawo i w lewo
                if c < 60:
                    App.left_finger += 1
                if c > 60:
                    App.left_finger = 0
            # draw lines around hand
            cv2.line(roi, start, end, [0, 255, 0], 2)

        fingers += 1
        print(str(App.left_finger))
        if 15000 > hand_area > 13000 and 20 > handless_area > 13 and fingers == 1:
            wynik = 'Start'
        elif hand_area > 20000 and 33 > handless_area > 20 and fingers >= 4:
            wynik = 'Stop'
        elif 20000 > hand_area > 15000 and 20 > handless_area > 10 and fingers == 1 and App.left_finger == 0:
            wynik = 'Następny'
        elif 20000 > hand_area > 15000 and 20 > handless_area > 10 and fingers == 1 and App.left_finger > 0:
            wynik = 'Poprzedni'
        else:
            wynik = 'Nie rozpoznano gestu'

        self.t.insert(tk.INSERT, wynik + "\n" + str(hand_area) + "\n" + str(handless_area) + "\n" + str(fingers) + "\n")
        print(wynik + "\n" + str(hand_area) + "\n" + str(handless_area) + "\n" + str(fingers) + "\n")
        # sterowanie prezentacja
        presentation.presentation_control(wynik)
        if ret:
            # Rysowanie obrazu z kamery
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.photo2 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.photo3 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(mask))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.canvas2.create_image(0, 0, image=self.photo2, anchor=tk.NW)
            self.canvas3.create_image(0, 0, image=self.photo3, anchor=tk.NW)

        self.window.after(self.delay, self.update)


class MyVideoCapture:
    def __init__(self, video_source):
        # otwieram wideo w tym przypadku video_source = 0 bo kamera
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        ret, frame = self.vid.read()
        if ret:
            return (ret, frame)
        else:
            return (ret, None)

    def __del__(self):
        self.vid.release()


def otworzPlik():
    App(root, "Wideo", 0)


root = tk.Tk()
root.geometry("1400x900+10+10")
root.resizable(width=True, height=True)
btn = tk.Button(root, text='Włącz kamerę', width=20, bg="#ad527b", fg="#ffffff", command=otworzPlik).place(x=5, y=5)
canvas = tk.Canvas(root, width=650, height=400)
canvas.place(x=160)
canvas2 = tk.Canvas(root, width=650, height=400)
canvas2.place(x=160, y=400)

canvas3 = tk.Canvas(root, width=250, height=250)
canvas3.place(x=800)

canvasStart = tk.Canvas(root, width=200, height=200)
canvasStart.place(x=800)

# Pomocniczo rysuje gesty używane w programie
img = Image.open("start.png")
img = img.resize((150, 150), Image.ANTIALIAS)
img = ImageTk.PhotoImage(img)
panel = tk.Label(root, image=img)
panel.image = img
panel.place(x=1, y=100)

img = Image.open("stop.png")
img = img.resize((150, 150), Image.ANTIALIAS)
img = ImageTk.PhotoImage(img)
panel = tk.Label(root, image=img)
panel.image = img
panel.place(x=1, y=270)

img = Image.open("next.png")
img = img.resize((150, 150), Image.ANTIALIAS)
img = ImageTk.PhotoImage(img)
panel = tk.Label(root, image=img)
panel.image = img
panel.place(x=1, y=440)

img = Image.open("back.png")
img = img.resize((150, 150), Image.ANTIALIAS)
img = ImageTk.PhotoImage(img)
panel = tk.Label(root, image=img)
panel.image = img
panel.place(x=1, y=610)

yscrollbar = tk.Scrollbar(root)
yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

root.mainloop()
