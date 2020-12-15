# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 13:10:13 2020

@author: gmart
"""

import win32com.client as win32
import time


#prezentacja musi być włączona zanim wywołamy kod
#tutaj definiujemy sciezke do pliku - zakladam, ze jest w folderze projektu
filename = 'start.pptx'

powerpoint = win32.Dispatch('PowerPoint.Application')
presentation = powerpoint.Presentations.Open(FileName=filename, ReadOnly=1)
presentation.SlideShowSettings.Run()



def presentation_control(wynik):
    if wynik == 'Start':
        #pierwszy slajd
        presentation.SlideShowWindow.View.First()
    elif wynik == 'Stop':
        #koniec pokazu slajdów
        presentation.SlideShowWindow.View.Exit()
        powerpoint.Quit()
    elif wynik == 'Następny':
        #następny slajd
        presentation.SlideShowWindow.View.Next()
    elif wynik == 'Poprzedni':
        #poprzedni slajd
        presentation.SlideShowWindow.View.Previous()
    else:
        time.sleep(1)
        #nic sie nie dzieje przez 1 s, jesli nie rozpoznano gestu
       
    
#***test***       
#time.sleep(2)
#presentation_control('Start')
#time.sleep(2)
#presentation_control('Następny')
#time.sleep(2)
#presentation_control('Poprzedni')
#time.sleep(2)
#presentation_control('Stop')