__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import ConfigParser as configparser
import os.path

from Cura.util import profile
from Cura.util import resources

class simpleModePanel(wx.Panel):
	"Main user interface window for Quickprint mode"
	def __init__(self, parent, callback):
		super(simpleModePanel, self).__init__(parent)
		self._callback = callback

		self._print_profile_options = []
		self._print_material_options = []

		printTypePanel = wx.Panel(self)
		for filename in resources.getSimpleModeProfiles():
			cp = configparser.ConfigParser()
			cp.read(filename)
			base_filename = os.path.splitext(os.path.basename(filename))[0]
			name = base_filename
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.RadioButton(printTypePanel, -1, name, style=wx.RB_GROUP if len(self._print_profile_options) == 0 else 0)
			button.base_filename = base_filename
			button.filename = filename
			self._print_profile_options.append(button)
			if profile.getPreference('simpleModeProfile') == base_filename:
				button.SetValue(True)

		printMaterialPanel = wx.Panel(self)
		for filename in resources.getSimpleModeMaterials():
			cp = configparser.ConfigParser()
			cp.read(filename)
			base_filename = os.path.splitext(os.path.basename(filename))[0]
			name = base_filename
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.RadioButton(printMaterialPanel, -1, name, style=wx.RB_GROUP if len(self._print_material_options) == 0 else 0)
			button.base_filename = base_filename
			button.filename = filename
			self._print_material_options.append(button)
			if profile.getPreference('simpleModeMaterial') == base_filename:
				button.SetValue(True)

		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			printMaterialPanel.Show(False)
		
		self.printSupport = wx.CheckBox(self, -1, _("Print support structure"))
		self.printBrim = wx.CheckBox(self, -1, _("Print brim"))
		# self.printRaft = wx.CheckBox(self, -1, _("Print raft"))



		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)

		sb = wx.StaticBox(printTypePanel, label=_("Select a quickprint profile:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		for button in self._print_profile_options:
			boxsizer.Add(button)
		printTypePanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printTypePanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printTypePanel, (0,0), flag=wx.EXPAND)

		sb = wx.StaticBox(printMaterialPanel, label=_("Material:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		for button in self._print_material_options:
			boxsizer.Add(button)
		printMaterialPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printMaterialPanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printMaterialPanel, (1,0), flag=wx.EXPAND)

		sb = wx.StaticBox(self, label=_("Other:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.Add(self.printSupport)
		boxsizer.Add(self.printBrim)
		# boxsizer.Add(self.printRaft)

		sizer.Add(boxsizer, (2,0), flag=wx.EXPAND)

		for button in self._print_profile_options:
			button.Bind(wx.EVT_RADIOBUTTON, self._update)
		for button in self._print_material_options:
			button.Bind(wx.EVT_RADIOBUTTON, self._update)

		self.printSupport.Bind(wx.EVT_CHECKBOX, self._update)
		self.printBrim.Bind(wx.EVT_CHECKBOX, self._update)
		# self.printRaft.Bind(wx.EVT_CHECKBOX, self._update)

	def _update(self, e):
		for button in self._print_profile_options:
			if button.GetValue():
				profile.putPreference('simpleModeProfile', button.base_filename)
		for button in self._print_material_options:
			if button.GetValue():
				profile.putPreference('simpleModeMaterial', button.base_filename)
		self._callback()

	def getSettingOverrides(self):
		settings = {}
		for setting in profile.settingsList:
			if not setting.isProfile():
				continue
			settings[setting.getName()] = setting.getDefault()

		for button in self._print_profile_options:
			if button.GetValue():
				cp = configparser.ConfigParser()
				cp.read(button.filename)
				for setting in profile.settingsList:
					if setting.isProfile():
						if cp.has_option('profile', setting.getName()):
							settings[setting.getName()] = cp.get('profile', setting.getName())
		if profile.getMachineSetting('gcode_flavor') != 'UltiGCode':
			for button in self._print_material_options:
				if button.GetValue():
					cp = configparser.ConfigParser()
					cp.read(button.filename)
					for setting in profile.settingsList:
						if setting.isProfile():
							if cp.has_option('profile', setting.getName()):
								settings[setting.getName()] = cp.get('profile', setting.getName())

		if self.printSupport.GetValue():
			settings['support'] = "Everywhere"#"Exterior Only"
		if self.printBrim.GetValue():
			settings['platform_adhesion'] = "Brim"
		# if self.printRaft.GetValue():
		# 	settings['platform_adhesion'] = "Raft"
		

		if profile.getMachineSetting('gcode_flavor') != 'UltiGCode':
			settings['start.gcode'] = """;This Gcode has been generated specifically for the Creatable D2
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Filament Diameter: {filament_diameter}
;Nozzle Size: {nozzle_size}
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
M106                         ; start with the fan on
G28						 ; Go Home
G92 E0                       ; set extruder position to 0
M104 S{print_temperature}	 ; set extruder temp
M140 S{print_bed_temperature}; get bed heating up
G1 Z100 F5000
G1 X-125
G1 Z1
M109 S{print_temperature}    ; set extruder temp and wait
M190 S{print_bed_temperature}; get bed heating up and wait
G92 E-32
G1 E0 F400
G1 E50 F200
G1 F1000
G1 X-125
G92 E0
"""
			settings['end.gcode'] = """
M400
G28
M104 S0                                      ; hotend off
M140 S0                                      ; heated bed heater off (if you have it)
M107                                         ; fans off
G92 E0                      			     ; set extruder to 0
G1 E-3 F300                  			     ; retract a bit to relieve pressure
M84                                          ; steppers off
G90                                          ; absolute positioning
;{profile_string}
"""
		if profile.getMachineSetting('machine_type') == 'creatableD2':
			settings['start.gcode'] = """;This Gcode has been generated specifically for the Creatable D2
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Filament Diameter: {filament_diameter}
;Nozzle Size: {nozzle_size}
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
M106                         ; start with the fan on
G28						 ; Go Home
G92 E0                       ; set extruder position to 0
M104 S{print_temperature}	 ; set extruder temp
M140 S{print_bed_temperature}; get bed heating up
G1 Z100 F5000
G1 X-125
G1 Z1
M109 S{print_temperature}    ; set extruder temp and wait
M190 S{print_bed_temperature}; get bed heating up and wait
G92 E-32
G1 E0 F400
G1 E50 F200
G1 F1000
G1 X-125
G92 E0
"""
			settings['end.gcode'] = """
M400
G28
M104 S0                                      ; hotend off
M140 S0                                      ; heated bed heater off (if you have it)
M107                                         ; fans off
G92 E0                      			     ; set extruder to 0
G1 E-3 F300                  			     ; retract a bit to relieve pressure
M84                                          ; steppers off
G90                                          ; absolute positioning
;{profile_string}
"""

		if profile.getMachineSetting('machine_type') == 'creatableD3':
			settings['start.gcode'] = """;This Gcode has been generated specifically for the Creatable D3
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Filament Diameter: {filament_diameter}
;Nozzle Size: {nozzle_size}
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
M106 S255                    ; start with the fan on
G28						 ; Go Home
G92 E0                       ; set extruder position to 0
M104 S{print_temperature}	 ; set extruder temp
M140 S{print_bed_temperature}; get bed heating up
G1 Z100 F5000
G1 X-135
G1 Z{bottom_thickness}
M109 S{print_temperature}    ; set extruder temp and wait
M190 S{print_bed_temperature}; get bed heating up and wait
G92 E-32
G1 E0 F400
G1 E50 F200
G1 F1000
G1 X-125
G92 E0
"""
			settings['end.gcode'] = """
M400
G28
M104 S0                                      ; hotend off
M140 S0                                      ; heated bed heater off (if you have it)
M107                                         ; fans off
G92 E0                      			     ; set extruder to 0
G1 E-3 F300                  			     ; retract a bit to relieve pressure
M84                                          ; steppers off
G90                                          ; absolute positioning
;{profile_string}
"""

		return settings

	def updateProfileToControls(self):
		pass
