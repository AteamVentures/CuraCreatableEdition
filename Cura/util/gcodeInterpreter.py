"""
The GCodeInterpreter module generates layer information from GCode.
It does this by parsing the whole GCode file. On large files this can take a while and should be used from a thread.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import sys
import math
import os
import time
import numpy
import types
import cStringIO as StringIO

from Cura.util import profile

def gcodePath(newType, pathType, layerThickness, startPoint):
	"""
	Build a gcodePath object. This used to be objects, however, this code is timing sensitive and dictionaries proved to be faster.
	"""
	if layerThickness <= 0.0:
		layerThickness = 0.01
	if profile.getProfileSetting('spiralize') == 'True':
		layerThickness = profile.getProfileSettingFloat('layer_height')
	return {'type': newType,
			'pathType': pathType,
			'layerThickness': layerThickness,
			'points': [startPoint],
			'extrusion': [0.0]}

class gcode(object):
	"""
	The heavy lifting GCode parser. This is most likely the hardest working python code in Cura.
	It parses a GCode file and stores the result in layers where each layer as paths that describe the GCode.
	"""
	def __init__(self):
		self.regMatch = {}
		self.layerList = None
		self.extrusionAmount = 0
		self.filename = None
		self.progressCallback = None
	
	def load(self, data):
		self.filename = None
		if type(data) in types.StringTypes and os.path.isfile(data):
			self.filename = data
			self._fileSize = os.stat(data).st_size
			gcodeFile = open(data, 'r')
			self._load(gcodeFile)
			gcodeFile.close()
		elif type(data) is list:
			self._load(data)
		else:
			self._fileSize = len(data)
			data.seekStart()
			self._load(data)

	def calculateWeight(self):
		#Calculates the weight of the filament in kg
		radius = float(profile.getProfileSetting('filament_diameter')) / 2
		volumeM3 = (self.extrusionAmount * (math.pi * radius * radius)) / (1000*1000*1000)
		return volumeM3 * profile.getPreferenceFloat('filament_physical_density')
	
	def calculateCost(self):
		cost_kg = profile.getPreferenceFloat('filament_cost_kg')
		cost_meter = profile.getPreferenceFloat('filament_cost_meter')
		if cost_kg > 0.0 and cost_meter > 0.0:
			return "%.2f / %.2f" % (self.calculateWeight() * cost_kg, self.extrusionAmount / 1000 * cost_meter)
		elif cost_kg > 0.0:
			return "%.2f" % (self.calculateWeight() * cost_kg)
		elif cost_meter > 0.0:
			return "%.2f" % (self.extrusionAmount / 1000 * cost_meter)
		return None
	
	def _load(self, gcodeFile):
		self.layerList = []
		pos = [0.0,0.0,0.0]
		posOffset = [0.0, 0.0, 0.0]
		currentE = 0.0
		currentExtruder = 0
		extrudeAmountMultiply = 1.0
		absoluteE = True
		scale = 1.0
		posAbs = True
		feedRate = 3600.0
		moveType = 'move'
		layerThickness = 0.1
		pathType = 'CUSTOM'
		currentLayer = []
		currentPath = gcodePath('move', pathType, layerThickness, pos)
		currentPath['extruder'] = currentExtruder

		currentLayer.append(currentPath)
		for line in gcodeFile:
			if type(line) is tuple:
				line = line[0]

			#Parse Cura_SF comments
			if line.startswith(';TYPE:'):
				pathType = line[6:].strip()

			if ';' in line:
				comment = line[line.find(';')+1:].strip()
				#Slic3r GCode comment parser
				if comment == 'fill':
					pathType = 'FILL'
				elif comment == 'perimeter':
					pathType = 'WALL-INNER'
				elif comment == 'skirt':
					pathType = 'SKIRT'
				#Cura layer comments.
				if comment.startswith('LAYER:'):
					currentPath = gcodePath(moveType, pathType, layerThickness, currentPath['points'][-1])
					layerThickness = 0.0
					currentPath['extruder'] = currentExtruder
					for path in currentLayer:
						path['points'] = numpy.array(path['points'], numpy.float32)
						path['extrusion'] = numpy.array(path['extrusion'], numpy.float32)
					self.layerList.append(currentLayer)
					if self.progressCallback is not None:
						if self.progressCallback(float(gcodeFile.tell()) / float(self._fileSize)):
							#Abort the loading, we can safely return as the results here will be discarded
							gcodeFile.close()
							return
					currentLayer = [currentPath]
				line = line[0:line.find(';')]

			G = getCodeInt(line, 'G')
			if G is not None:
				if G == 0 or G == 1:	#Move
					x = getCodeFloat(line, 'X')
					y = getCodeFloat(line, 'Y')
					z = getCodeFloat(line, 'Z')
					e = getCodeFloat(line, 'E')
					#f = getCodeFloat(line, 'F')
					oldPos = pos
					pos = pos[:]
					if posAbs:
						if x is not None:
							pos[0] = x * scale + posOffset[0]
						if y is not None:
							pos[1] = y * scale + posOffset[1]
						if z is not None:
							pos[2] = z * scale + posOffset[2]
					else:
						if x is not None:
							pos[0] += x * scale
						if y is not None:
							pos[1] += y * scale
						if z is not None:
							pos[2] += z * scale
					moveType = 'move'
					if e is not None:
						if absoluteE and posAbs:
							e -= currentE
						if e > 0.0:
							moveType = 'extrude'
						if e < 0.0:
							moveType = 'retract'
						currentE += e
					else:
						e = 0.0
					if moveType == 'move' and oldPos[2] != pos[2]:
						if oldPos[2] > pos[2] and abs(oldPos[2] - pos[2]) > 5.0 and pos[2] < 1.0:
							oldPos[2] = 0.0
						if layerThickness == 0.0:
							layerThickness = abs(oldPos[2] - pos[2])
					if currentPath['type'] != moveType or currentPath['pathType'] != pathType:
						currentPath = gcodePath(moveType, pathType, layerThickness, currentPath['points'][-1])
						currentPath['extruder'] = currentExtruder
						currentLayer.append(currentPath)

					currentPath['points'].append(pos)
					currentPath['extrusion'].append(e * extrudeAmountMultiply)
				elif G == 4:	#Delay
					S = getCodeFloat(line, 'S')
					P = getCodeFloat(line, 'P')
				elif G == 10:	#Retract
					currentPath = gcodePath('retract', pathType, layerThickness, currentPath['points'][-1])
					currentPath['extruder'] = currentExtruder
					currentLayer.append(currentPath)
					currentPath['points'].append(currentPath['points'][0])
				elif G == 11:	#Push back after retract
					pass
				elif G == 20:	#Units are inches
					scale = 25.4
				elif G == 21:	#Units are mm
					scale = 1.0
				elif G == 28:	#Home
					x = getCodeFloat(line, 'X')
					y = getCodeFloat(line, 'Y')
					z = getCodeFloat(line, 'Z')
					center = [0.0,0.0,0.0]
					if x is None and y is None and z is None:
						pos = center
					else:
						pos = pos[:]
						if x is not None:
							pos[0] = center[0]
						if y is not None:
							pos[1] = center[1]
						if z is not None:
							pos[2] = center[2]
				elif G == 90:	#Absolute position
					posAbs = True
				elif G == 91:	#Relative position
					posAbs = False
				elif G == 92:
					x = getCodeFloat(line, 'X')
					y = getCodeFloat(line, 'Y')
					z = getCodeFloat(line, 'Z')
					e = getCodeFloat(line, 'E')
					if e is not None:
						currentE = e
					#if x is not None:
					#	posOffset[0] = pos[0] - x
					#if y is not None:
					#	posOffset[1] = pos[1] - y
					#if z is not None:
					#	posOffset[2] = pos[2] - z
				else:
					print "Unknown G code:" + str(G)
			else:
				M = getCodeInt(line, 'M')
				if M is not None:
					if M == 0:	#Message with possible wait (ignored)
						pass
					elif M == 1:	#Message with possible wait (ignored)
						pass
					elif M == 25:	#Stop SD printing
						pass
					elif M == 80:	#Enable power supply
						pass
					elif M == 81:	#Suicide/disable power supply
						pass
					elif M == 82:   #Absolute E
						absoluteE = True
					elif M == 83:   #Relative E
						absoluteE = False
					elif M == 84:	#Disable step drivers
						pass
					elif M == 92:	#Set steps per unit
						pass
					elif M == 101:	#Enable extruder
						pass
					elif M == 103:	#Disable extruder
						pass
					elif M == 104:	#Set temperature, no wait
						pass
					elif M == 105:	#Get temperature
						pass
					elif M == 106:	#Enable fan
						pass
					elif M == 107:	#Disable fan
						pass
					elif M == 108:	#Extruder RPM (these should not be in the final GCode, but they are)
						pass
					elif M == 109:	#Set temperature, wait
						pass
					elif M == 110:	#Reset N counter
						pass
					elif M == 113:	#Extruder PWM (these should not be in the final GCode, but they are)
						pass
					elif M == 117:	#LCD message
						pass
					elif M == 140:	#Set bed temperature
						pass
					elif M == 190:	#Set bed temperature & wait
						pass
					elif M == 221:	#Extrude amount multiplier
						s = getCodeFloat(line, 'S')
						if s is not None:
							extrudeAmountMultiply = s / 100.0
					else:
						print "Unknown M code:" + str(M)
				else:
					T = getCodeInt(line, 'T')
					if T is not None:
						if currentExtruder > 0:
							posOffset[0] -= profile.getMachineSettingFloat('extruder_offset_x%d' % (currentExtruder))
							posOffset[1] -= profile.getMachineSettingFloat('extruder_offset_y%d' % (currentExtruder))
						currentExtruder = T
						if currentExtruder > 0:
							posOffset[0] += profile.getMachineSettingFloat('extruder_offset_x%d' % (currentExtruder))
							posOffset[1] += profile.getMachineSettingFloat('extruder_offset_y%d' % (currentExtruder))

		for path in currentLayer:
			path['points'] = numpy.array(path['points'], numpy.float32)
			path['extrusion'] = numpy.array(path['extrusion'], numpy.float32)
		self.layerList.append(currentLayer)
		if self.progressCallback is not None and self._fileSize > 0:
			self.progressCallback(float(gcodeFile.tell()) / float(self._fileSize))

def getCodeInt(line, code):
	n = line.find(code) + 1
	if n < 1:
		return None
	m = line.find(' ', n)
	try:
		if m < 0:
			return int(line[n:])
		return int(line[n:m])
	except:
		return None

def getCodeFloat(line, code):
	n = line.find(code) + 1
	if n < 1:
		return None
	m = line.find(' ', n)
	try:
		if m < 0:
			return float(line[n:])
		return float(line[n:m])
	except:
		return None

if __name__ == '__main__':
	t = time.time()
	for filename in sys.argv[1:]:
		g = gcode()
		g.load(filename)
	print time.time() - t

