## 🚚
import os
import re
import threading
import time
import psutil
import requests
import pystray
from pystray 		import MenuItem as item
from PIL    		import Image
from configparser 	import ConfigParser
from inspect 		import getfullargspec
from win32gui 		import GetWindowText, EnumWindows
from win32process	import GetWindowThreadProcessId


config = ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cfg', 'config.ini'))

UPDATE_INTERVAL = config.getint('Main', 'update_interval')
FINISH_TRESHOLD = config.getint('Main', 'finish_treshold')
STOP_TRESHOLD	= config.getint('Main', 'stop_treshold')
IS_COMPANION 		= config.getboolean('Main', 'end_if_target_process_not_running')
WEB_HOOK		= config.get('IFTTT', 'web_hook')

## String literal which helps to find the Keyshot process
KEYSHOT = "keyshot.exe"

## Callbacks for render status and render time
render_init = None
reached_last_frame = None

## Regex to catch current render status
## 💡 Localization is unimportant since the matched keywords are always in english (as of Keyshot 8.2.0) 		
RENDER_WINDOW 		= re.compile(r'\"([^)]+)\"')
RENDERING_ACTIVE	= re.compile(r'\"(.*?)\" \[(.*?)\] \([^\d]*(\d+)%\)') 											## "foo1.jpg" [1920 x 1080] (Rendering 50%)
ANIMATION_ACTIVE 	= re.compile(r'\"([^)]+)\" \([^\d]*(\d+)/[0-9]\) \[([^)]+)\] \(([^)]+)\)$') 					## "bar1.3.jpg" (Animation Frame 3/6) [1920 x 1080] (Rendering 50%)
RENDERING_FINISHED	= re.compile(r'\"([^)]+)\" \[([^)]+)\] \((\bRendering done\b|(Saving)[^)]+)\)') 				## "foo1.jpg" [1920 x 1080] (Saving foo1.jpg)
ANIMATION_FINISHED	= re.compile(r'\"([^)]+)\" \(([^)]+)\) \[([^)]+)\] \((\bRendering done\b|(Saving)[^)]+)\)') 	## "bar1.6.jpg" (Animation frame 6/6) [1920 x 1080] (Saving bar1.6.jpg (Animation frame 5/5))
PROCESSING_FRAMES 	= re.compile(r'\"([^)]+)\" \(([^)]+)\) \[([^)]+)\]$') 											## "bar1.jpg" (Animation frame 3/6) [1920 x 1080]
TOTAL_FRAMES 		= re.compile(r'\"([^)]+)\" \([^\d]*[0-9]/(\d+)\) \[([^)]+)\] \(([^)]+)\)')						## Get total frame count


class Ifjobdone:

	def __init__(self, callback=None, **kwargs):
		self.windowHandle = None
		self.callback = callback
		self.rendering = None
		self.animation = None
		self._callbackArgCount = len(getfullargspec(self.callback).args)
		if("self" in getfullargspec(self.callback).args):
			self._callbackArgCount -= 1
		self._stopMonitoring = threading.Event()
		self._findWindowHandleAttempts = 0
		self.updateWindowHandle()

		if(self.callback):
			threading.Thread(target=self._monitor, args=(self.callback, self._stopMonitoring)).start()


	## Properties

	@property
	def windowHandle(self):
		return self._windowHandle

	@property
	def rendering(self):
		return self._rendering
	
	@property
	def animation(self):
		return self._animation


	## Setters

	@windowHandle.setter
	def windowHandle(self, value):
		self._windowHandle = value

	@rendering.setter
	def rendering(self, value):
		self._rendering = str(value)
		
	@animation.setter
	def animation(self, value):
		self._animation = str(value)


	## Functions

	def stopMonitoring(self):
		self._stopMonitoring.set()

	def stopExec():
		scriptPid = os.getpid()
		scriptProcess = psutil.Process(scriptPid)
		print("IFJD has been exited.")
		scriptProcess.terminate() 
		
	def IsProcessRunning(self, processName):
		'''
		Iterates through the running processes
		and returns True if process is found.
		'''
		for proc in psutil.process_iter():
			try:
				# Check if process name contains the given name string.
				if processName.lower() in proc.name().lower():
					return True
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				pass
		return False

	def elapsedTime(self):	
		'''
		Returns the total render time.
		'''
		startTime = render_init
		stopTime = time.time()
		duration = stopTime - startTime
		return round(duration,1)
	

	## Taskbar Icon Stuff

	def setup(icon):
		icon.visible = True
		Ifjobdone(monitorKeyshot)

	def iconOpenConfig():
		os.startfile(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cfg', 'config.ini'))

	def iconExit():
		icon.visible = False
		Ifjobdone.stopExec()

	def updateWindowHandle(self, callback=None):
		'''
		Iterates through top-level windows
		and sets handle if default render window is found.
		'''
		def getKeyshotHandle(handle, extra):
			processPid	 = GetWindowThreadProcessId(handle)[1]
			processName  = psutil.Process(processPid).name().lower()
			renderWindow = RENDER_WINDOW.match(GetWindowText(handle))
			if(KEYSHOT in processName and renderWindow):
				self.windowHandle = handle
				## Should really be a return False here to kill off the 
				## 	enumeration when a suitable handle is found, but that
				## 	produces a weird 'Things have gone VERY wrong' error.
				##	See: http://docs.activestate.com/activepython/3.1/pywin32/win32gui__EnumWindows_meth.html	(/@naschorr)

		EnumWindows(getKeyshotHandle, None)

		## Checks if Keyshot.exe is still running
		if(IS_COMPANION):
			if(not self.IsProcessRunning(KEYSHOT)):
				icon.visible = False
				Ifjobdone.stopExec()
		
		if(not self.windowHandle):
			self._findWindowHandleAttempts += 1
			time.sleep(UPDATE_INTERVAL)	
			self.updateWindowHandle()

		if(callback):
			callback()


	def checkRenderStatus(self, callback=None):
		'''
		Checks if Keyshot render window title
		matches one of the regex expressions.
		'''
		windowTitle = GetWindowText(self.windowHandle)
		##	|
		renderingActive 	= RENDERING_ACTIVE.match(windowTitle) 
		renderingFinished 	= RENDERING_FINISHED.match(windowTitle)
		animationActive 	= ANIMATION_ACTIVE.match(windowTitle)		
		animationFinished 	= ANIMATION_FINISHED.match(windowTitle)		
		processingFrames	= PROCESSING_FRAMES.match(windowTitle)
		totalFrames 		= TOTAL_FRAMES.match(windowTitle)

		renderCallback = {0:"No active job", 1:"Image render in progress", 2: "Animation render in progress"}
		
## 🏷️ 	TO-DO: Remove globals, they don't get passed through func since the function gets fired every X seconds
		global render_init	
		global reached_last_frame

		if(not windowTitle): 
			callback(renderCallback[0])
			self.updateWindowHandle()
		
		## 🖼️ Image render active
		if(renderingActive):
			renderFile		  = renderingActive.group(1)
			renderRes 		  = renderingActive.group(2)
			renderingProgress = renderingActive.group(3)

			## Initiates timer, gets reset after the job is finished or stopped	
			if render_init is None:
				render_init = time.time()
				print(f"Starting rendering: {renderFile} ({renderRes})")	

			## Check if title updated
			if(self.rendering != renderingProgress):
				self.rendering = renderingProgress

				if(callback):
					callback(renderCallback[1])
				
		## 🎞️ Animation render active
		if(animationActive):
			animFile 	 = animationActive.group(1)
			animRes 	 = animationActive.group(3)
			currentFrame = animationActive.group(2)
			totalFrames  = totalFrames.group(2)

			## Check if title updated
			if(self.animation != currentFrame):
				self.animation = currentFrame
				if render_init is None:
					render_init = time.time()
					print(f"Starting animation: {animFile} ({animRes}), Total frames: {totalFrames})")	

				if(callback):
					callback(renderCallback[2])	
						
					if(currentFrame == totalFrames):
						reached_last_frame = True
			
		## ✅ Render or animation is finished
		if(renderingFinished and render_init is not None) or (animationFinished and reached_last_frame):

			renderTime = self.elapsedTime()

			if(renderTime > FINISH_TRESHOLD):
				if(renderingFinished):
					renderFile = renderingFinished.group(1)
					print(f"Rendering done, taking {renderTime} seconds.")
					try:
						requests.post(WEB_HOOK,params={"value1":renderFile,"value2":(round(renderTime,1))})
## 🏷️ 				TO-DO: Handle Exceptions properly (ConnectionError, SocketError, ...)
					except Exception:
						print("Couldn't reach web hook. No internet connection or wrong URL?")

				if(animationFinished):
					animFile   = animationFinished.group(1)
					print(f"Animation done, taking {renderTime} seconds.")
					try:
						requests.post(WEB_HOOK,params={"value1":animFile,"value2":(round(renderTime,1))})
					except Exception:
						print("Couldn't reach web hook. No internet connection or wrong URL?")
			else:
				print(f"Job done after {renderTime} seconds, but notification treshold ({FINISH_TRESHOLD} seconds) was not met.")

			render_init, reached_last_frame = None, None ## Reset
			
		## ❌ Render or animation stopped (stopped by user or process was killed)
		if(render_init is not None and not windowTitle):

			renderTime = self.elapsedTime()

			if(renderTime > STOP_TRESHOLD):
				print(f"Rendering stopped after {renderTime} seconds.")
			else:
				print(f"Rendering stopped after {renderTime} seconds, but notification treshold ({STOP_TRESHOLD} seconds) was not met.")

			render_init, reached_last_frame = None, None ## Reset
			
	def _monitor(self, callback, stopMonitoring_event):
		while(not stopMonitoring_event.is_set()):
			self.checkRenderStatus(callback)
			time.sleep(UPDATE_INTERVAL)

def monitorKeyshot(render_status):
	print(render_status)
	icon.title = render_status
	icon.update_menu()

## Taskbar icon / pystray
icon 		= pystray.Icon("If Job Done")
icon.menu 	= (item('Open config', Ifjobdone.iconOpenConfig), item('Exit', Ifjobdone.iconExit))
icon.icon 	= Image.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'tray.ico'))
icon.title 	= "IFJD ready" 

icon.run(Ifjobdone.setup)