__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import webbrowser
import threading
import time
import math

import wx
import wx.wizard

from Cura.gui import firmwareInstall
from Cura.gui import printWindow
from Cura.util import machineCom
from Cura.util import profile
from Cura.util import gcodeGenerator
from Cura.util import resources


class InfoBox(wx.Panel):
	def __init__(self, parent):
		super(InfoBox, self).__init__(parent)
		self.SetBackgroundColour('#FFFF80')

		self.sizer = wx.GridBagSizer(5, 5)
		self.SetSizer(self.sizer)

		self.attentionBitmap = wx.Bitmap(resources.getPathForImage('attention.png'))
		self.errorBitmap = wx.Bitmap(resources.getPathForImage('error.png'))
		self.readyBitmap = wx.Bitmap(resources.getPathForImage('ready.png'))
		self.busyBitmap = [
			wx.Bitmap(resources.getPathForImage('busy-0.png')),
			wx.Bitmap(resources.getPathForImage('busy-1.png')),
			wx.Bitmap(resources.getPathForImage('busy-2.png')),
			wx.Bitmap(resources.getPathForImage('busy-3.png'))
		]

		self.bitmap = wx.StaticBitmap(self, -1, wx.EmptyBitmapRGBA(24, 24, red=255, green=255, blue=255, alpha=1))
		self.text = wx.StaticText(self, -1, '')
		self.extraInfoButton = wx.Button(self, -1, 'i', style=wx.BU_EXACTFIT)
		self.sizer.Add(self.bitmap, pos=(0, 0), flag=wx.ALL, border=5)
		self.sizer.Add(self.text, pos=(0, 1), flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.Add(self.extraInfoButton, pos=(0,2), flag=wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.AddGrowableCol(1)

		self.extraInfoButton.Show(False)

		self.extraInfoUrl = ''
		self.busyState = None
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.doBusyUpdate, self.timer)
		self.Bind(wx.EVT_BUTTON, self.doExtraInfo, self.extraInfoButton)
		self.timer.Start(100)

	def SetInfo(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.Refresh()

	def SetError(self, info, extraInfoUrl):
		self.extraInfoUrl = extraInfoUrl
		self.SetBackgroundColour('#FF8080')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(True)
		self.Layout()
		self.SetErrorIndicator()
		self.Refresh()

	def SetAttention(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.SetAttentionIndicator()
		self.Layout()
		self.Refresh()

	def SetBusy(self, info):
		self.SetInfo(info)
		self.SetBusyIndicator()

	def SetBusyIndicator(self):
		self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def doExtraInfo(self, e):
		webbrowser.open(self.extraInfoUrl)

	def doBusyUpdate(self, e):
		if self.busyState is None:
			return
		self.busyState += 1
		if self.busyState >= len(self.busyBitmap):
			self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def SetReadyIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.readyBitmap)

	def SetErrorIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.errorBitmap)

	def SetAttentionIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.attentionBitmap)


class InfoPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent, title):
		wx.wizard.WizardPageSimple.__init__(self, parent)

		sizer = wx.GridBagSizer(5, 5)
		self.sizer = sizer
		self.SetSizer(sizer)

		title = wx.StaticText(self, -1, title)
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		sizer.Add(title, pos=(0, 0), span=(1, 2), flag=wx.ALIGN_CENTRE | wx.ALL)
		sizer.Add(wx.StaticLine(self, -1), pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		sizer.AddGrowableCol(1)

		self.rowNr = 2

	def AddText(self, info):
		text = wx.StaticText(self, -1, info)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return text

	def AddSeperator(self):
		self.GetSizer().Add(wx.StaticLine(self, -1), pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1

	def AddHiddenSeperator(self):
		self.AddText("")

	def AddInfoBox(self):
		infoBox = InfoBox(self)
		self.GetSizer().Add(infoBox, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
		self.rowNr += 1
		return infoBox

	def AddRadioButton(self, label, style=0):
		radio = wx.RadioButton(self, -1, label, style=style)
		self.GetSizer().Add(radio, pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1
		return radio

	def AddCheckbox(self, label, checked=False):
		check = wx.CheckBox(self, -1)
		text = wx.StaticText(self, -1, label)
		check.SetValue(checked)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 2), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AddButton(self, label):
		button = wx.Button(self, -1, label)
		self.GetSizer().Add(button, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return button

	def AddDualButton(self, label1, label2):
		button1 = wx.Button(self, -1, label1)
		self.GetSizer().Add(button1, pos=(self.rowNr, 0), flag=wx.RIGHT)
		button2 = wx.Button(self, -1, label2)
		self.GetSizer().Add(button2, pos=(self.rowNr, 1))
		self.rowNr += 1
		return button1, button2

	def AddTextCtrl(self, value):
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(ret, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddLabelTextCtrl(self, info, value):
		text = wx.StaticText(self, -1, info)
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(ret, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddTextCtrlButton(self, value, buttonText):
		text = wx.TextCtrl(self, -1, value)
		button = wx.Button(self, -1, buttonText)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(button, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return text, button

	def AddBitmap(self, bitmap):
		bitmap = wx.StaticBitmap(self, -1, bitmap)
		self.GetSizer().Add(bitmap, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return bitmap

	def AddCheckmark(self, label, bitmap):
		check = wx.StaticBitmap(self, -1, bitmap)
		text = wx.StaticText(self, -1, label)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 1), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AddCombo(self, label, options):
		combo = wx.ComboBox(self, -1, options[0], choices=options, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		text = wx.StaticText(self, -1, label)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(combo, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return combo

	def AllowNext(self):
		return True

	def AllowBack(self):
		return True

	def StoreData(self):
		pass


class FirstInfoPage(InfoPage):
	def __init__(self, parent, addNew):
		if addNew:
			super(FirstInfoPage, self).__init__(parent, _("Add new machine wizard"))
		else:
			super(FirstInfoPage, self).__init__(parent, _("First time run wizard"))
			self.AddText(_("Welcome, and thanks for trying Cura!"))
			self.AddSeperator()
		self.AddText(_("This wizard will help you in setting up Cura for your machine."))
		if not addNew:
			self.AddSeperator()
			self._language_option = self.AddCombo(_("Select your language:"), map(lambda o: o[1], resources.getLanguageOptions()))
		else:
			self._language_option = None
		# self.AddText(_("This wizard will help you with the following steps:"))
		# self.AddText(_("* Configure Cura for your machine"))
		# self.AddText(_("* Optionally upgrade your firmware"))
		# self.AddText(_("* Optionally check if your machine is working safely"))
		# self.AddText(_("* Optionally level your printer bed"))

		#self.AddText('* Calibrate your machine')
		#self.AddText('* Do your first print')

	def AllowBack(self):
		return False

	def StoreData(self):
		if self._language_option is not None:
			profile.putPreference('language', self._language_option.GetValue())
			resources.setupLocalization(self._language_option.GetValue())

class PrintrbotPage(InfoPage):
	def __init__(self, parent):
		self._printer_info = [
			# X, Y, Z, Nozzle Size, Filament Diameter, PrintTemperature, Print Speed, Travel Speed, Retract speed, Retract amount, use bed level sensor
			("Simple Metal", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			("Metal Plus", 250, 250, 250, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			("Simple Makers Kit", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			(":" + _("Older models"),),
			("Original", 130, 130, 130, 0.5, 2.95, 208, 40, 70, 30, 1, False),
			("Simple Maker's Edition v1", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Simple Maker's Edition v2 (2013 Printrbot Simple)", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Simple Maker's Edition v3 (2014 Printrbot Simple)", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Jr v1", 115, 120, 80, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Jr v2", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("LC v1", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("LC v2", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v1", 200, 200, 200, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v2", 200, 200, 200, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v2.1", 185, 220, 200, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v2.2 (Model 1404/140422/140501/140507)", 250, 250, 250, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			("Go v2 Large", 505, 306, 310, 0.4, 1.75, 208, 35, 70, 30, 1, True),
		]

		super(PrintrbotPage, self).__init__(parent, _("Printrbot Selection"))
		# self.AddBitmap(wx.Bitmap(resources.getPathForImage('Printrbot_logo.png')))
		self.AddText(_("Select which Printrbot machine you have:"))
		self._items = []
		for printer in self._printer_info:
			if printer[0].startswith(":"):
				self.AddSeperator()
				self.AddText(printer[0][1:])
			else:
				item = self.AddRadioButton(printer[0])
				item.data = printer[1:]
				self._items.append(item)

	def StoreData(self):
		profile.putMachineSetting('machine_name', 'Printrbot ???')
		for item in self._items:
			if item.GetValue():
				data = item.data
				profile.putMachineSetting('machine_name', 'Printrbot ' + item.GetLabel())
				profile.putMachineSetting('machine_width', data[0])
				profile.putMachineSetting('machine_depth', data[1])
				profile.putMachineSetting('machine_height', data[2])
				profile.putProfileSetting('nozzle_size', data[3])
				profile.putProfileSetting('filament_diameter', data[4])
				profile.putProfileSetting('print_temperature', data[5])
				profile.putProfileSetting('print_speed', data[6])
				profile.putProfileSetting('travel_speed', data[7])
				profile.putProfileSetting('retraction_speed', data[8])
				profile.putProfileSetting('retraction_amount', data[9])
				profile.putProfileSetting('wall_thickness', float(profile.getProfileSettingFloat('nozzle_size')) * 2)
				profile.putMachineSetting('has_heated_bed', 'False')
				profile.putMachineSetting('machine_center_is_zero', 'False')
				profile.putMachineSetting('extruder_head_size_min_x', '0')
				profile.putMachineSetting('extruder_head_size_min_y', '0')
				profile.putMachineSetting('extruder_head_size_max_x', '0')
				profile.putMachineSetting('extruder_head_size_max_y', '0')
				profile.putMachineSetting('extruder_head_size_height', '0')
				if data[10]:
					profile.setAlterationFile('start.gcode', """;Sliced at: {day} {date} {time}
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Print time: {print_time}
;Filament used: {filament_amount}m {filament_weight}g
;Filament cost: {filament_cost}
;M190 S{print_bed_temperature} ;Uncomment to add your own bed temperature line
;M109 S{print_temperature} ;Uncomment to add your own temperature line
G21        ;metric values
G90        ;absolute positioning
M82        ;set extruder to absolute mode
M107       ;start with the fan off
G28 X0 Y0  ;move X/Y to min endstops
G28 Z0     ;move Z to min endstops
G29        ;Run the auto bed leveling
G1 Z15.0 F{travel_speed} ;move the platform down 15mm
G92 E0                  ;zero the extruded length
G1 F200 E3              ;extrude 3mm of feed stock
G92 E0                  ;zero the extruded length again
G1 F{travel_speed}
;Put printing message on LCD screen
M117 Printing...
""")

class OtherMachineSelectPage(InfoPage):
	def __init__(self, parent):
		super(OtherMachineSelectPage, self).__init__(parent, _("Other machine information"))
		self.AddText(_("The following pre-defined machine profiles are available"))
		self.AddText(_("Note that these profiles are not guaranteed to give good results,\nor work at all. Extra tweaks might be required.\nIf you find issues with the predefined profiles,\nor want an extra profile.\nPlease report it at the github issue tracker."))
		self.options = []
		machines = resources.getDefaultMachineProfiles()
		machines.sort()
		for filename in machines:
			name = os.path.splitext(os.path.basename(filename))[0]
			item = self.AddRadioButton(name)
			item.filename = filename
			item.Bind(wx.EVT_RADIOBUTTON, self.OnProfileSelect)
			self.options.append(item)
		self.AddSeperator()
		item = self.AddRadioButton(_('Custom...'))
		item.SetValue(True)
		item.Bind(wx.EVT_RADIOBUTTON, self.OnOtherSelect)

	def OnProfileSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().otherMachineInfoPage)

	def OnOtherSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().customRepRapInfoPage)

	def StoreData(self):
		for option in self.options:
			if option.GetValue():
				profile.loadProfile(option.filename)
				profile.loadMachineSettings(option.filename)

class OtherMachineInfoPage(InfoPage):
	def __init__(self, parent):
		super(OtherMachineInfoPage, self).__init__(parent, _("Cura Ready!"))
		self.AddText(_("Cura is now ready to be used!"))

class CustomRepRapInfoPage(InfoPage):
	def __init__(self, parent):
		super(CustomRepRapInfoPage, self).__init__(parent, _("Custom RepRap information"))
		self.AddText(_("RepRap machines can be vastly different, so here you can set your own settings."))
		self.AddText(_("Be sure to review the default profile before running it on your machine."))
		self.AddText(_("If you like a default profile for your machine added,\nthen make an issue on github."))
		self.AddSeperator()
		self.AddText(_("You will have to manually install Marlin or Sprinter firmware."))
		self.AddSeperator()
		self.machineName = self.AddLabelTextCtrl(_("Machine name"), "RepRap")
		self.machineWidth = self.AddLabelTextCtrl(_("Machine width X (mm)"), "80")
		self.machineDepth = self.AddLabelTextCtrl(_("Machine depth Y (mm)"), "80")
		self.machineHeight = self.AddLabelTextCtrl(_("Machine height Z (mm)"), "55")
		self.nozzleSize = self.AddLabelTextCtrl(_("Nozzle size (mm)"), "0.5")
		self.heatedBed = self.AddCheckbox(_("Heated bed"))
		self.HomeAtCenter = self.AddCheckbox(_("Bed center is 0,0,0 (RoStock)"))

	def StoreData(self):
		profile.putMachineSetting('machine_name', self.machineName.GetValue())
		profile.putMachineSetting('machine_width', self.machineWidth.GetValue())
		profile.putMachineSetting('machine_depth', self.machineDepth.GetValue())
		profile.putMachineSetting('machine_height', self.machineHeight.GetValue())
		profile.putProfileSetting('nozzle_size', self.nozzleSize.GetValue())
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSettingFloat('nozzle_size')) * 2)
		profile.putMachineSetting('has_heated_bed', str(self.heatedBed.GetValue()))
		profile.putMachineSetting('machine_center_is_zero', str(self.HomeAtCenter.GetValue()))
		profile.putMachineSetting('extruder_head_size_min_x', '0')
		profile.putMachineSetting('extruder_head_size_min_y', '0')
		profile.putMachineSetting('extruder_head_size_max_x', '0')
		profile.putMachineSetting('extruder_head_size_max_y', '0')
		profile.putMachineSetting('extruder_head_size_height', '0')
		profile.checkAndUpdateMachineName()

class MachineSelectPage(InfoPage):
	def __init__(self, parent):
		super(MachineSelectPage, self).__init__(parent, _("Select your machine"))
		self.AddText(_("What kind of machine do you have:"))
		self.CreatableD3Radio = self.AddRadioButton("CREATABLE D3", style=wx.RB_GROUP)
		self.CreatableD3Radio.Bind(wx.EVT_RADIOBUTTON, self.OnCreatableD3Select)
		self.CreatableD3Radio.SetValue(True)
		self.CreatableD2Radio = self.AddRadioButton("CREATABLE D2")
		self.CreatableD2Radio.Bind(wx.EVT_RADIOBUTTON, self.OnCreatableD2Select)
		self.Ultimaker2Radio = self.AddRadioButton("Ultimaker2")
		self.Ultimaker2Radio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		self.Ultimaker2ExtRadio = self.AddRadioButton("Ultimaker2extended")
		self.Ultimaker2ExtRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		self.Ultimaker2GoRadio = self.AddRadioButton("Ultimaker2go")
		self.Ultimaker2GoRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		self.UltimakerRadio = self.AddRadioButton("Ultimaker Original")
		self.UltimakerRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerSelect)
		self.UltimakerOPRadio = self.AddRadioButton("Ultimaker Original+")
		self.UltimakerOPRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerOPSelect)
		self.PrintrbotRadio = self.AddRadioButton("Printrbot")
		self.PrintrbotRadio.Bind(wx.EVT_RADIOBUTTON, self.OnPrintrbotSelect)
		self.LulzbotTazRadio = self.AddRadioButton("Lulzbot TAZ")
		self.LulzbotTazRadio.Bind(wx.EVT_RADIOBUTTON, self.OnLulzbotSelect)
		self.LulzbotMiniRadio = self.AddRadioButton("Lulzbot Mini")
		self.LulzbotMiniRadio.Bind(wx.EVT_RADIOBUTTON, self.OnLulzbotSelect)
		self.OtherRadio = self.AddRadioButton(_("Other (Ex: RepRap, MakerBot, Witbox)"))
		self.OtherRadio.Bind(wx.EVT_RADIOBUTTON, self.OnOtherSelect)

		# self.Ultimaker2Radio = self.AddRadioButton("Ultimaker2", style=wx.RB_GROUP)
		# self.Ultimaker2Radio.SetValue(True)
		# self.Ultimaker2Radio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		# self.Ultimaker2ExtRadio = self.AddRadioButton("Ultimaker2extended")
		# self.Ultimaker2ExtRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		# self.Ultimaker2GoRadio = self.AddRadioButton("Ultimaker2go")
		# self.Ultimaker2GoRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		# self.UltimakerRadio = self.AddRadioButton("Ultimaker Original")
		# self.UltimakerRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerSelect)
		# self.UltimakerOPRadio = self.AddRadioButton("Ultimaker Original+")
		# self.UltimakerOPRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerOPSelect)
		# self.PrintrbotRadio = self.AddRadioButton("Printrbot")
		# self.PrintrbotRadio.Bind(wx.EVT_RADIOBUTTON, self.OnPrintrbotSelect)
		# self.LulzbotTazRadio = self.AddRadioButton("Lulzbot TAZ")
		# self.LulzbotTazRadio.Bind(wx.EVT_RADIOBUTTON, self.OnLulzbotSelect)
		# self.LulzbotMiniRadio = self.AddRadioButton("Lulzbot Mini")
		# self.LulzbotMiniRadio.Bind(wx.EVT_RADIOBUTTON, self.OnLulzbotSelect)
		# self.OtherRadio = self.AddRadioButton(_("Other (Ex: RepRap, MakerBot, Witbox)"))
		# self.OtherRadio.Bind(wx.EVT_RADIOBUTTON, self.OnOtherSelect)
		# self.AddSeperator()
		# self.AddText(_("The collection of anonymous usage information helps with the continued improvement of Cura."))
		# self.AddText(_("This does NOT submit your models online nor gathers any privacy related information."))
		# self.SubmitUserStats = self.AddCheckbox(_("Submit anonymous usage information:"))
		# self.AddText(_("For full details see: http://wiki.ultimaker.com/Cura:stats"))
		# self.SubmitUserStats.SetValue(True)

	def OnUltimaker2Select(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimaker2ReadyPage)

	def OnUltimakerSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimakerSelectParts)

	def OnUltimakerOPSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimakerFirmwareUpgradePage)

	def OnPrintrbotSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().printrbotSelectType)

	def OnLulzbotSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotReadyPage)

	def OnCreatableD2Select(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().creatableReadyPage)
	def OnCreatableD3Select(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().creatableReadyPage)

	def OnOtherSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().otherMachineSelectPage)

	def AllowNext(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().creatableReadyPage)
		return True

	def StoreData(self):
		profile.putProfileSetting('retraction_enable', 'True')
		if self.Ultimaker2Radio.GetValue() or self.Ultimaker2GoRadio.GetValue() or self.Ultimaker2ExtRadio.GetValue():
			if self.Ultimaker2Radio.GetValue():
				profile.putMachineSetting('machine_width', '230')
				profile.putMachineSetting('machine_depth', '225')
				profile.putMachineSetting('machine_height', '205')
				profile.putMachineSetting('machine_name', 'ultimaker2')
				profile.putMachineSetting('machine_type', 'ultimaker2')
				profile.putMachineSetting('has_heated_bed', 'True')
			if self.Ultimaker2GoRadio.GetValue():
				profile.putMachineSetting('machine_width', '120')
				profile.putMachineSetting('machine_depth', '120')
				profile.putMachineSetting('machine_height', '115')
				profile.putMachineSetting('machine_name', 'ultimaker2go')
				profile.putMachineSetting('machine_type', 'ultimaker2go')
				profile.putMachineSetting('has_heated_bed', 'False')
			if self.Ultimaker2ExtRadio.GetValue():
				profile.putMachineSetting('machine_width', '230')
				profile.putMachineSetting('machine_depth', '225')
				profile.putMachineSetting('machine_height', '315')
				profile.putMachineSetting('machine_name', 'ultimaker2extended')
				profile.putMachineSetting('machine_type', 'ultimaker2extended')
				profile.putMachineSetting('has_heated_bed', 'False')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'UltiGCode')
			profile.putMachineSetting('extruder_head_size_min_x', '40.0')
			profile.putMachineSetting('extruder_head_size_min_y', '10.0')
			profile.putMachineSetting('extruder_head_size_max_x', '60.0')
			profile.putMachineSetting('extruder_head_size_max_y', '30.0')
			profile.putMachineSetting('extruder_head_size_height', '48.0')
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putProfileSetting('fan_full_height', '5.0')
			profile.putMachineSetting('extruder_offset_x1', '18.0')
			profile.putMachineSetting('extruder_offset_y1', '0.0')
		elif self.UltimakerRadio.GetValue():
			profile.putMachineSetting('machine_width', '205')
			profile.putMachineSetting('machine_depth', '205')
			profile.putMachineSetting('machine_height', '200')
			profile.putMachineSetting('machine_name', 'ultimaker original')
			profile.putMachineSetting('machine_type', 'ultimaker')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putMachineSetting('extruder_head_size_min_x', '75.0')
			profile.putMachineSetting('extruder_head_size_min_y', '18.0')
			profile.putMachineSetting('extruder_head_size_max_x', '18.0')
			profile.putMachineSetting('extruder_head_size_max_y', '35.0')
			profile.putMachineSetting('extruder_head_size_height', '55.0')
		elif self.UltimakerOPRadio.GetValue():
			profile.putMachineSetting('machine_width', '205')
			profile.putMachineSetting('machine_depth', '205')
			profile.putMachineSetting('machine_height', '200')
			profile.putMachineSetting('machine_name', 'ultimaker original+')
			profile.putMachineSetting('machine_type', 'ultimaker_plus')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putMachineSetting('extruder_head_size_min_x', '75.0')
			profile.putMachineSetting('extruder_head_size_min_y', '18.0')
			profile.putMachineSetting('extruder_head_size_max_x', '18.0')
			profile.putMachineSetting('extruder_head_size_max_y', '35.0')
			profile.putMachineSetting('extruder_head_size_height', '55.0')
			profile.putMachineSetting('has_heated_bed', 'True')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putProfileSetting('retraction_enable', 'True')
		elif self.LulzbotTazRadio.GetValue() or self.LulzbotMiniRadio.GetValue():
			if self.LulzbotTazRadio.GetValue():
				profile.putMachineSetting('machine_width', '298')
				profile.putMachineSetting('machine_depth', '275')
				profile.putMachineSetting('machine_height', '250')
				profile.putProfileSetting('nozzle_size', '0.35')
				profile.putMachineSetting('machine_name', 'Lulzbot TAZ')
			else:
				profile.putMachineSetting('machine_width', '160')
				profile.putMachineSetting('machine_depth', '160')
				profile.putMachineSetting('machine_height', '160')
				profile.putProfileSetting('nozzle_size', '0.5')
				profile.putMachineSetting('machine_name', 'Lulzbot Mini')
			profile.putMachineSetting('machine_type', 'Aleph Objects')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putMachineSetting('has_heated_bed', 'True')
			profile.putMachineSetting('extruder_head_size_min_x', '0.0')
			profile.putMachineSetting('extruder_head_size_min_y', '0.0')
			profile.putMachineSetting('extruder_head_size_max_x', '0.0')
			profile.putMachineSetting('extruder_head_size_max_y', '0.0')
			profile.putMachineSetting('extruder_head_size_height', '0.0')

		elif self.CreatableD2Radio.GetValue() or 0:
			#machine settings
			if self.CreatableD2Radio.GetValue():
				profile.putMachineSetting('machine_width', '200')
				profile.putMachineSetting('machine_depth', '200')
				profile.putMachineSetting('machine_height', '160')
				profile.putMachineSetting('machine_name', 'Creatable D2')
				profile.putMachineSetting('machine_type', 'creatableD2')
				profile.putMachineSetting('serial_baud', '250000')
			profile.putMachineSetting('machine_center_is_zero', 'True')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putMachineSetting('has_heated_bed', 'True')
			profile.putMachineSetting('extruder_head_size_min_x', '42')
			profile.putMachineSetting('extruder_head_size_min_y', '38')
			profile.putMachineSetting('extruder_head_size_max_x', '42')
			profile.putMachineSetting('extruder_head_size_max_y', '38')
			profile.putMachineSetting('extruder_head_size_height', '50')
			profile.putMachineSetting('machine_shape', 'Circular')
			profile.putMachineSetting('steps_per_e', '0')
			#print settings 
			# - basic -
			profile.putProfileSetting('layer_height', '0.1')
			profile.putProfileSetting('wall_thickness','0.8')
			profile.putProfileSetting('retraction_enable','True')
			profile.putProfileSetting('solid_layer_thickness','0.6')
			profile.putProfileSetting('fill_density','20')
			profile.putProfileSetting('print_speed','50')
			profile.putProfileSetting('print_temperature','210')
			profile.putProfileSetting('print_bed_temperature','75')
			profile.putProfileSetting('support','None')
			profile.putProfileSetting('platform_adhesion','None')
			profile.putProfileSetting('filament_diameter','1.75')
			profile.putProfileSetting('filament_flow','100')
			# - advanced -	
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putProfileSetting('retraction_speed','40')
			profile.putProfileSetting('retraction_amount','4.5')
			profile.putProfileSetting('bottom_thickness','0.3')
			profile.putProfileSetting('layer0_width_factor','100')
			profile.putProfileSetting('object_sink','0.0')
			profile.putProfileSetting('overlap_dual','0.15')
			profile.putProfileSetting('travel_speed','150')
			profile.putProfileSetting('bottom_layer_speed','20')
			profile.putProfileSetting('infill_speed','0.0')
			profile.putProfileSetting('inset0_speed','0.0')
			profile.putProfileSetting('insetx_speed','0.0')
			profile.putProfileSetting('cool_min_layer_time','5')
			profile.putProfileSetting('fan_enabled','True')
			profile.setAlterationFile('start.gcode', """;This Gcode has been generated specifically for the Creatable D2
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
G1 X-125
G1 Z1
M109 S{print_temperature}    ; set extruder temp and wait
M190 S{print_bed_temperature}; get bed heating up and wait
G92 E-32
G1 E0 F1000
G1 E70 F200
G1 F5000
G1 X-100
G92 E0
""")

		elif self.CreatableD3Radio.GetValue() or 0:
			#machine settings
			if self.CreatableD3Radio.GetValue():
				profile.putMachineSetting('machine_width', '250')
				profile.putMachineSetting('machine_depth', '250')
				profile.putMachineSetting('machine_height', '200')
				profile.putMachineSetting('machine_name', 'Creatable D3')
				profile.putMachineSetting('machine_type', 'creatableD3')
				profile.putMachineSetting('serial_baud', '250000')
			profile.putMachineSetting('machine_center_is_zero', 'True')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putMachineSetting('has_heated_bed', 'True')
			profile.putMachineSetting('extruder_head_size_min_x', '42')
			profile.putMachineSetting('extruder_head_size_min_y', '41')
			profile.putMachineSetting('extruder_head_size_max_x', '42')
			profile.putMachineSetting('extruder_head_size_max_y', '41')
			profile.putMachineSetting('extruder_head_size_height', '43')
			profile.putMachineSetting('machine_shape', 'Circular')
			profile.putMachineSetting('steps_per_e', '0')
			#print settings 
			# - basic -
			profile.putProfileSetting('layer_height', '0.1')
			profile.putProfileSetting('wall_thickness','0.8')
			profile.putProfileSetting('retraction_enable','True')
			profile.putProfileSetting('solid_layer_thickness','0.6')
			profile.putProfileSetting('fill_density','20')
			profile.putProfileSetting('print_speed','50')
			profile.putProfileSetting('print_temperature','210')
			profile.putProfileSetting('print_bed_temperature','75')
			profile.putProfileSetting('support','None')
			profile.putProfileSetting('platform_adhesion','None')
			profile.putProfileSetting('filament_diameter','1.75')
			profile.putProfileSetting('filament_flow','100')
			# - advanced -	
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putProfileSetting('retraction_speed','40')
			profile.putProfileSetting('retraction_amount','4.5')
			profile.putProfileSetting('bottom_thickness','0.3')
			profile.putProfileSetting('layer0_width_factor','100')
			profile.putProfileSetting('object_sink','0.0')
			profile.putProfileSetting('overlap_dual','0.15')
			profile.putProfileSetting('travel_speed','150')
			profile.putProfileSetting('bottom_layer_speed','20')
			profile.putProfileSetting('infill_speed','0.0')
			profile.putProfileSetting('inset0_speed','0.0')
			profile.putProfileSetting('insetx_speed','0.0')
			profile.putProfileSetting('cool_min_layer_time','5')
			profile.putProfileSetting('fan_enabled','True')
			profile.setAlterationFile('start.gcode', """;This Gcode has been generated specifically for the Creatable D3
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
G1 X-130
G1 Z1
M109 S{print_temperature}    ; set extruder temp and wait
M190 S{print_bed_temperature}; get bed heating up and wait
G92 E-32
G1 E0 F1000
G1 E70 F200
G1 F5000
G1 X-100
G92 E0
""")
			# profile.putProfileSetting('pre_extrude_x','-130')
			# profile.putMachineSetting('pre_extrude_x','-130')

		else:
			profile.putMachineSetting('machine_width', '80')
			profile.putMachineSetting('machine_depth', '80')
			profile.putMachineSetting('machine_height', '60')
			profile.putMachineSetting('machine_name', 'reprap')
			profile.putMachineSetting('machine_type', 'reprap')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putPreference('startMode', 'Normal')
			profile.putProfileSetting('nozzle_size', '0.5')
		profile.checkAndUpdateMachineName()
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSetting('nozzle_size')) * 2)
		# if self.SubmitUserStats.GetValue():
		# 	profile.putPreference('submit_slice_information', 'True')
		# else:
		# 	profile.putPreference('submit_slice_information', 'False')


class SelectParts(InfoPage):
	def __init__(self, parent):
		super(SelectParts, self).__init__(parent, _("Select upgraded parts you have"))
		self.AddText(_("To assist you in having better default settings for your Ultimaker\nCura would like to know which upgrades you have in your machine."))
		self.AddSeperator()
		self.springExtruder = self.AddCheckbox(_("Extruder drive upgrade"))
		self.heatedBedKit = self.AddCheckbox(_("Heated printer bed (kit)"))
		self.heatedBed = self.AddCheckbox(_("Heated printer bed (self built)"))
		self.dualExtrusion = self.AddCheckbox(_("Dual extrusion (experimental)"))
		self.AddSeperator()
		self.AddText(_("If you have an Ultimaker bought after october 2012 you will have the\nExtruder drive upgrade. If you do not have this upgrade,\nit is highly recommended to improve reliability."))
		self.AddText(_("This upgrade can be bought from the Ultimaker webshop\nor found on thingiverse as thing:26094"))
		self.springExtruder.SetValue(True)

	def StoreData(self):
		profile.putMachineSetting('ultimaker_extruder_upgrade', str(self.springExtruder.GetValue()))
		if self.heatedBed.GetValue() or self.heatedBedKit.GetValue():
			profile.putMachineSetting('has_heated_bed', 'True')
		else:
			profile.putMachineSetting('has_heated_bed', 'False')
		if self.dualExtrusion.GetValue():
			profile.putMachineSetting('extruder_amount', '2')
			profile.putMachineSetting('machine_depth', '195')
		else:
			profile.putMachineSetting('extruder_amount', '1')
		if profile.getMachineSetting('ultimaker_extruder_upgrade') == 'True':
			profile.putProfileSetting('retraction_enable', 'True')
		else:
			profile.putProfileSetting('retraction_enable', 'False')


class UltimakerFirmwareUpgradePage(InfoPage):
	def __init__(self, parent):
		super(UltimakerFirmwareUpgradePage, self).__init__(parent, _("Upgrade Ultimaker Firmware"))
		self.AddText(_("Firmware is the piece of software running directly on your 3D printer.\nThis firmware controls the step motors, regulates the temperature\nand ultimately makes your printer work."))
		self.AddHiddenSeperator()
		self.AddText(_("The firmware shipping with new Ultimakers works, but upgrades\nhave been made to make better prints, and make calibration easier."))
		self.AddHiddenSeperator()
		self.AddText(_("Cura requires these new features and thus\nyour firmware will most likely need to be upgraded.\nYou will get the chance to do so now."))
		upgradeButton, skipUpgradeButton = self.AddDualButton('Upgrade to Marlin firmware', 'Skip upgrade')
		upgradeButton.Bind(wx.EVT_BUTTON, self.OnUpgradeClick)
		skipUpgradeButton.Bind(wx.EVT_BUTTON, self.OnSkipClick)
		self.AddHiddenSeperator()
		if profile.getMachineSetting('machine_type') == 'ultimaker':
			self.AddText(_("Do not upgrade to this firmware if:"))
			self.AddText(_("* You have an older machine based on ATMega1280 (Rev 1 machine)"))
			self.AddText(_("* Build your own heated bed"))
			self.AddText(_("* Have other changes in the firmware"))
#		button = self.AddButton('Goto this page for a custom firmware')
#		button.Bind(wx.EVT_BUTTON, self.OnUrlClick)

	def AllowNext(self):
		return False

	def OnUpgradeClick(self, e):
		if firmwareInstall.InstallFirmware():
			self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()

	def OnSkipClick(self, e):
		self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()
		self.GetParent().ShowPage(self.GetNext())

	def OnUrlClick(self, e):
		webbrowser.open('http://marlinbuilder.robotfuzz.com/')

class UltimakerCheckupPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCheckupPage, self).__init__(parent, _("Ultimaker Checkup"))

		self.checkBitmap = wx.Bitmap(resources.getPathForImage('checkmark.png'))
		self.crossBitmap = wx.Bitmap(resources.getPathForImage('cross.png'))
		self.unknownBitmap = wx.Bitmap(resources.getPathForImage('question.png'))
		self.endStopNoneBitmap = wx.Bitmap(resources.getPathForImage('endstop_none.png'))
		self.endStopXMinBitmap = wx.Bitmap(resources.getPathForImage('endstop_xmin.png'))
		self.endStopXMaxBitmap = wx.Bitmap(resources.getPathForImage('endstop_xmax.png'))
		self.endStopYMinBitmap = wx.Bitmap(resources.getPathForImage('endstop_ymin.png'))
		self.endStopYMaxBitmap = wx.Bitmap(resources.getPathForImage('endstop_ymax.png'))
		self.endStopZMinBitmap = wx.Bitmap(resources.getPathForImage('endstop_zmin.png'))
		self.endStopZMaxBitmap = wx.Bitmap(resources.getPathForImage('endstop_zmax.png'))

		self.AddText(
			_("It is a good idea to do a few sanity checks now on your Ultimaker.\nYou can skip these if you know your machine is functional."))
		b1, b2 = self.AddDualButton(_("Run checks"), _("Skip checks"))
		b1.Bind(wx.EVT_BUTTON, self.OnCheckClick)
		b2.Bind(wx.EVT_BUTTON, self.OnSkipClick)
		self.AddSeperator()
		self.commState = self.AddCheckmark(_("Communication:"), self.unknownBitmap)
		self.tempState = self.AddCheckmark(_("Temperature:"), self.unknownBitmap)
		self.stopState = self.AddCheckmark(_("Endstops:"), self.unknownBitmap)
		self.AddSeperator()
		self.infoBox = self.AddInfoBox()
		self.machineState = self.AddText("")
		self.temperatureLabel = self.AddText("")
		self.errorLogButton = self.AddButton(_("Show error log"))
		self.errorLogButton.Show(False)
		self.AddSeperator()
		self.endstopBitmap = self.AddBitmap(self.endStopNoneBitmap)
		self.comm = None
		self.xMinStop = False
		self.xMaxStop = False
		self.yMinStop = False
		self.yMaxStop = False
		self.zMinStop = False
		self.zMaxStop = False

		self.Bind(wx.EVT_BUTTON, self.OnErrorLog, self.errorLogButton)

	def __del__(self):
		if self.comm is not None:
			self.comm.close()

	def AllowNext(self):
		self.endstopBitmap.Show(False)
		return False

	def OnSkipClick(self, e):
		self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()
		self.GetParent().ShowPage(self.GetNext())

	def OnCheckClick(self, e=None):
		self.errorLogButton.Show(False)
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnCheckClick)
			return
		self.infoBox.SetBusy(_("Connecting to machine."))
		self.commState.SetBitmap(self.unknownBitmap)
		self.tempState.SetBitmap(self.unknownBitmap)
		self.stopState.SetBitmap(self.unknownBitmap)
		self.checkupState = 0
		self.checkExtruderNr = 0
		self.comm = machineCom.MachineCom(callbackObject=self)

	def OnErrorLog(self, e):
		printWindow.LogWindow('\n'.join(self.comm.getLog()))

	def mcLog(self, message):
		pass

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if not self.comm.isOperational():
			return
		if self.checkupState == 0:
			self.tempCheckTimeout = 20
			if temp[self.checkExtruderNr] > 70:
				self.checkupState = 1
				wx.CallAfter(self.infoBox.SetInfo, _("Cooldown before temperature check."))
				self.comm.sendCommand("M104 S0 T%d" % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
			else:
				self.startTemp = temp[self.checkExtruderNr]
				self.checkupState = 2
				wx.CallAfter(self.infoBox.SetInfo, _("Checking the heater and temperature sensor."))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
		elif self.checkupState == 1:
			if temp[self.checkExtruderNr] < 60:
				self.startTemp = temp[self.checkExtruderNr]
				self.checkupState = 2
				wx.CallAfter(self.infoBox.SetInfo, _("Checking the heater and temperature sensor."))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
		elif self.checkupState == 2:
			#print "WARNING, TEMPERATURE TEST DISABLED FOR TESTING!"
			if temp[self.checkExtruderNr] > self.startTemp + 40:
				self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
				if self.checkExtruderNr < int(profile.getMachineSetting('extruder_amount')):
					self.checkExtruderNr = 0
					self.checkupState = 3
					wx.CallAfter(self.infoBox.SetAttention, _("Please make sure none of the endstops are pressed."))
					wx.CallAfter(self.endstopBitmap.Show, True)
					wx.CallAfter(self.Layout)
					self.comm.sendCommand('M119')
					wx.CallAfter(self.tempState.SetBitmap, self.checkBitmap)
				else:
					self.checkupState = 0
					self.checkExtruderNr += 1
			else:
				self.tempCheckTimeout -= 1
				if self.tempCheckTimeout < 1:
					self.checkupState = -1
					wx.CallAfter(self.tempState.SetBitmap, self.crossBitmap)
					wx.CallAfter(self.infoBox.SetError, _("Temperature measurement FAILED!"), 'http://wiki.ultimaker.com/Cura:_Temperature_measurement_problems')
					self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
					self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
		elif self.checkupState >= 3 and self.checkupState < 10:
			self.comm.sendCommand('M119')
		wx.CallAfter(self.temperatureLabel.SetLabel, _("Head temperature: %d") % (temp[self.checkExtruderNr]))

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			wx.CallAfter(self.commState.SetBitmap, self.checkBitmap)
			wx.CallAfter(self.machineState.SetLabel, _("Communication State: %s") % (self.comm.getStateString()))
		elif self.comm.isError():
			wx.CallAfter(self.commState.SetBitmap, self.crossBitmap)
			wx.CallAfter(self.infoBox.SetError, _("Failed to establish connection with the printer."), 'http://wiki.ultimaker.com/Cura:_Connection_problems')
			wx.CallAfter(self.endstopBitmap.Show, False)
			wx.CallAfter(self.machineState.SetLabel, '%s' % (self.comm.getErrorString()))
			wx.CallAfter(self.errorLogButton.Show, True)
			wx.CallAfter(self.Layout)
		else:
			wx.CallAfter(self.machineState.SetLabel, _("Communication State: %s") % (self.comm.getStateString()))

	def mcMessage(self, message):
		if self.checkupState >= 3 and self.checkupState < 10 and ('_min' in message or '_max' in message):
			for data in message.split(' '):
				if ':' in data:
					tag, value = data.split(':', 1)
					if tag == 'x_min':
						self.xMinStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'x_max':
						self.xMaxStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'y_min':
						self.yMinStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'y_max':
						self.yMaxStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'z_min':
						self.zMinStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'z_max':
						self.zMaxStop = (value == 'H' or value == 'TRIGGERED')
			if ':' in message:
				tag, value = map(str.strip, message.split(':', 1))
				if tag == 'x_min':
					self.xMinStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'x_max':
					self.xMaxStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'y_min':
					self.yMinStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'y_max':
					self.yMaxStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'z_min':
					self.zMinStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'z_max':
					self.zMaxStop = (value == 'H' or value == 'TRIGGERED')
			if 'z_max' in message:
				self.comm.sendCommand('M119')

			if self.checkupState == 3:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					if profile.getMachineSetting('machine_type') == 'ultimaker_plus':
						self.checkupState = 5
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the left X endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMinBitmap)
					else:
						self.checkupState = 4
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the right X endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMaxBitmap)
			elif self.checkupState == 4:
				if not self.xMinStop and self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 5
					wx.CallAfter(self.infoBox.SetAttention, _("Please press the left X endstop."))
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMinBitmap)
			elif self.checkupState == 5:
				if self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 6
					wx.CallAfter(self.infoBox.SetAttention, _("Please press the front Y endstop."))
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopYMinBitmap)
			elif self.checkupState == 6:
				if not self.xMinStop and not self.xMaxStop and self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					if profile.getMachineSetting('machine_type') == 'ultimaker_plus':
						self.checkupState = 8
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the top Z endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMinBitmap)
					else:
						self.checkupState = 7
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the back Y endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopYMaxBitmap)
			elif self.checkupState == 7:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 8
					wx.CallAfter(self.infoBox.SetAttention, _("Please press the top Z endstop."))
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMinBitmap)
			elif self.checkupState == 8:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and self.zMinStop and not self.zMaxStop:
					if profile.getMachineSetting('machine_type') == 'ultimaker_plus':
						self.checkupState = 10
						self.comm.close()
						wx.CallAfter(self.infoBox.SetInfo, _("Checkup finished"))
						wx.CallAfter(self.infoBox.SetReadyIndicator)
						wx.CallAfter(self.endstopBitmap.Show, False)
						wx.CallAfter(self.stopState.SetBitmap, self.checkBitmap)
						wx.CallAfter(self.OnSkipClick, None)
					else:
						self.checkupState = 9
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the bottom Z endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMaxBitmap)
			elif self.checkupState == 9:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and self.zMaxStop:
					self.checkupState = 10
					self.comm.close()
					wx.CallAfter(self.infoBox.SetInfo, _("Checkup finished"))
					wx.CallAfter(self.infoBox.SetReadyIndicator)
					wx.CallAfter(self.endstopBitmap.Show, False)
					wx.CallAfter(self.stopState.SetBitmap, self.checkBitmap)
					wx.CallAfter(self.OnSkipClick, None)

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass


class UltimakerCalibrationPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCalibrationPage, self).__init__(parent, _("Ultimaker Calibration"))

		self.AddText("Your Ultimaker requires some calibration.")
		self.AddText("This calibration is needed for a proper extrusion amount.")
		self.AddSeperator()
		self.AddText("The following values are needed:")
		self.AddText("* Diameter of filament")
		self.AddText("* Number of steps per mm of filament extrusion")
		self.AddSeperator()
		self.AddText("The better you have calibrated these values, the better your prints\nwill become.")
		self.AddSeperator()
		self.AddText("First we need the diameter of your filament:")
		self.filamentDiameter = self.AddTextCtrl(profile.getProfileSetting('filament_diameter'))
		self.AddText(
			"If you do not own digital Calipers that can measure\nat least 2 digits then use 2.89mm.\nWhich is the average diameter of most filament.")
		self.AddText("Note: This value can be changed later at any time.")

	def StoreData(self):
		profile.putProfileSetting('filament_diameter', self.filamentDiameter.GetValue())


class UltimakerCalibrateStepsPerEPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCalibrateStepsPerEPage, self).__init__(parent, _("Ultimaker Calibration"))

		#if profile.getMachineSetting('steps_per_e') == '0':
		#	profile.putMachineSetting('steps_per_e', '865.888')

		self.AddText(_("Calibrating the Steps Per E requires some manual actions."))
		self.AddText(_("First remove any filament from your machine."))
		self.AddText(_("Next put in your filament so the tip is aligned with the\ntop of the extruder drive."))
		self.AddText(_("We'll push the filament 100mm"))
		self.extrudeButton = self.AddButton(_("Extrude 100mm filament"))
		self.AddText(_("Now measure the amount of extruded filament:\n(this can be more or less then 100mm)"))
		self.lengthInput, self.saveLengthButton = self.AddTextCtrlButton("100", _("Save"))
		self.AddText(_("This results in the following steps per E:"))
		self.stepsPerEInput = self.AddTextCtrl(profile.getMachineSetting('steps_per_e'))
		self.AddText(_("You can repeat these steps to get better calibration."))
		self.AddSeperator()
		self.AddText(
			_("If you still have filament in your printer which needs\nheat to remove, press the heat up button below:"))
		self.heatButton = self.AddButton(_("Heatup for filament removal"))

		self.saveLengthButton.Bind(wx.EVT_BUTTON, self.OnSaveLengthClick)
		self.extrudeButton.Bind(wx.EVT_BUTTON, self.OnExtrudeClick)
		self.heatButton.Bind(wx.EVT_BUTTON, self.OnHeatClick)

	def OnSaveLengthClick(self, e):
		currentEValue = float(self.stepsPerEInput.GetValue())
		realExtrudeLength = float(self.lengthInput.GetValue())
		newEValue = currentEValue * 100 / realExtrudeLength
		self.stepsPerEInput.SetValue(str(newEValue))
		self.lengthInput.SetValue("100")

	def OnExtrudeClick(self, e):
		t = threading.Thread(target=self.OnExtrudeRun)
		t.daemon = True
		t.start()

	def OnExtrudeRun(self):
		self.heatButton.Enable(False)
		self.extrudeButton.Enable(False)
		currentEValue = float(self.stepsPerEInput.GetValue())
		self.comm = machineCom.MachineCom()
		if not self.comm.isOpen():
			wx.MessageBox(
				_("Error: Failed to open serial port to machine\nIf this keeps happening, try disconnecting and reconnecting the USB cable"),
				'Printer error', wx.OK | wx.ICON_INFORMATION)
			self.heatButton.Enable(True)
			self.extrudeButton.Enable(True)
			return
		while True:
			line = self.comm.readline()
			if line == '':
				return
			if 'start' in line:
				break
			#Wait 3 seconds for the SD card init to timeout if we have SD in our firmware but there is no SD card found.
		time.sleep(3)

		self.sendGCommand('M302') #Disable cold extrusion protection
		self.sendGCommand("M92 E%f" % (currentEValue))
		self.sendGCommand("G92 E0")
		self.sendGCommand("G1 E100 F600")
		time.sleep(15)
		self.comm.close()
		self.extrudeButton.Enable()
		self.heatButton.Enable()

	def OnHeatClick(self, e):
		t = threading.Thread(target=self.OnHeatRun)
		t.daemon = True
		t.start()

	def OnHeatRun(self):
		self.heatButton.Enable(False)
		self.extrudeButton.Enable(False)
		self.comm = machineCom.MachineCom()
		if not self.comm.isOpen():
			wx.MessageBox(
				_("Error: Failed to open serial port to machine\nIf this keeps happening, try disconnecting and reconnecting the USB cable"),
				'Printer error', wx.OK | wx.ICON_INFORMATION)
			self.heatButton.Enable(True)
			self.extrudeButton.Enable(True)
			return
		while True:
			line = self.comm.readline()
			if line == '':
				self.heatButton.Enable(True)
				self.extrudeButton.Enable(True)
				return
			if 'start' in line:
				break
			#Wait 3 seconds for the SD card init to timeout if we have SD in our firmware but there is no SD card found.
		time.sleep(3)

		self.sendGCommand('M104 S200') #Set the temperature to 200C, should be enough to get PLA and ABS out.
		wx.MessageBox(
			'Wait till you can remove the filament from the machine, and press OK.\n(Temperature is set to 200C)',
			'Machine heatup', wx.OK | wx.ICON_INFORMATION)
		self.sendGCommand('M104 S0')
		time.sleep(1)
		self.comm.close()
		self.heatButton.Enable(True)
		self.extrudeButton.Enable(True)

	def sendGCommand(self, cmd):
		self.comm.sendCommand(cmd) #Disable cold extrusion protection
		while True:
			line = self.comm.readline()
			if line == '':
				return
			if line.startswith('ok'):
				break

	def StoreData(self):
		profile.putPreference('steps_per_e', self.stepsPerEInput.GetValue())

class Ultimaker2ReadyPage(InfoPage):
	def __init__(self, parent):
		super(Ultimaker2ReadyPage, self).__init__(parent, _("Ultimaker2"))
		self.AddText(_('Congratulations on your the purchase of your brand new Ultimaker2.'))
		self.AddText(_('Cura is now ready to be used with your Ultimaker2.'))
		self.AddSeperator()

class LulzbotReadyPage(InfoPage):
	def __init__(self, parent):
		super(LulzbotReadyPage, self).__init__(parent, _("Lulzbot TAZ/Mini"))
		self.AddText(_('Cura is now ready to be used with your Lulzbot.'))
		self.AddSeperator()

class CreatableReadyPage(InfoPage):
	def __init__(self, parent):
		super(CreatableReadyPage, self).__init__(parent, _("Creatable"))
		self.AddText('Cura is now ready to be used with your Creatable 3D printer.')
		self.AddSeperator()
		self.AddText('For more information about using Cura with your Creatable')
		self.AddText('3D printer, please visit www.creatablelabs.com/support')
		self.AddSeperator()

class ConfigWizard(wx.wizard.Wizard):
	def __init__(self, addNew = False):
		super(ConfigWizard, self).__init__(None, -1, _("Configuration Wizard"))

		self._old_machine_index = int(profile.getPreferenceFloat('active_machine'))
		if addNew:
			profile.setActiveMachine(profile.getMachineCount())

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
		self.Bind(wx.wizard.EVT_WIZARD_CANCEL, self.OnCancel)

		self.firstInfoPage = FirstInfoPage(self, addNew)
		self.machineSelectPage = MachineSelectPage(self)
		self.ultimakerSelectParts = SelectParts(self)
		self.ultimakerFirmwareUpgradePage = UltimakerFirmwareUpgradePage(self)
		self.ultimakerCheckupPage = UltimakerCheckupPage(self)
		self.ultimakerCalibrationPage = UltimakerCalibrationPage(self)
		self.ultimakerCalibrateStepsPerEPage = UltimakerCalibrateStepsPerEPage(self)
		self.bedLevelPage = bedLevelWizardMain(self)
		self.headOffsetCalibration = headOffsetCalibrationPage(self)
		self.printrbotSelectType = PrintrbotPage(self)
		self.otherMachineSelectPage = OtherMachineSelectPage(self)
		self.customRepRapInfoPage = CustomRepRapInfoPage(self)
		self.otherMachineInfoPage = OtherMachineInfoPage(self)

		self.ultimaker2ReadyPage = Ultimaker2ReadyPage(self)
		self.lulzbotReadyPage = LulzbotReadyPage(self)
		self.creatableReadyPage = CreatableReadyPage(self)


		wx.wizard.WizardPageSimple.Chain(self.firstInfoPage, self.machineSelectPage)
		#wx.wizard.WizardPageSimple.Chain(self.machineSelectPage, self.ultimaker2ReadyPage)
		wx.wizard.WizardPageSimple.Chain(self.machineSelectPage, self.ultimakerSelectParts)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerSelectParts, self.ultimakerFirmwareUpgradePage)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerFirmwareUpgradePage, self.ultimakerCheckupPage)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerCheckupPage, self.bedLevelPage)
		#wx.wizard.WizardPageSimple.Chain(self.ultimakerCalibrationPage, self.ultimakerCalibrateStepsPerEPage)
		wx.wizard.WizardPageSimple.Chain(self.printrbotSelectType, self.otherMachineInfoPage)
		wx.wizard.WizardPageSimple.Chain(self.otherMachineSelectPage, self.customRepRapInfoPage)

		self.FitToPage(self.firstInfoPage)
		self.GetPageAreaSizer().Add(self.firstInfoPage)

		self.RunWizard(self.firstInfoPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()

	def OnCancel(self, e):
		profile.setActiveMachine(self._old_machine_index)

class bedLevelWizardMain(InfoPage):
	def __init__(self, parent):
		super(bedLevelWizardMain, self).__init__(parent, _("Bed leveling wizard"))

		self.AddText(_('This wizard will help you in leveling your printer bed'))
		self.AddSeperator()
		self.AddText(_('It will do the following steps'))
		self.AddText(_('* Move the printer head to each corner'))
		self.AddText(_('  and let you adjust the height of the bed to the nozzle'))
		self.AddText(_('* Print a line around the bed to check if it is level'))
		self.AddSeperator()

		self.connectButton = self.AddButton(_('Connect to printer'))
		self.comm = None

		self.infoBox = self.AddInfoBox()
		self.resumeButton = self.AddButton(_('Resume'))
		self.upButton, self.downButton = self.AddDualButton(_('Up 0.2mm'), _('Down 0.2mm'))
		self.upButton2, self.downButton2 = self.AddDualButton(_('Up 10mm'), _('Down 10mm'))
		self.resumeButton.Enable(False)

		self.upButton.Enable(False)
		self.downButton.Enable(False)
		self.upButton2.Enable(False)
		self.downButton2.Enable(False)

		self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connectButton)
		self.Bind(wx.EVT_BUTTON, self.OnResume, self.resumeButton)
		self.Bind(wx.EVT_BUTTON, self.OnBedUp, self.upButton)
		self.Bind(wx.EVT_BUTTON, self.OnBedDown, self.downButton)
		self.Bind(wx.EVT_BUTTON, self.OnBedUp2, self.upButton2)
		self.Bind(wx.EVT_BUTTON, self.OnBedDown2, self.downButton2)

	def OnConnect(self, e = None):
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnConnect)
			return
		self.connectButton.Enable(False)
		self.comm = machineCom.MachineCom(callbackObject=self)
		self.infoBox.SetBusy(_('Connecting to machine.'))
		self._wizardState = 0

	def OnBedUp(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z9.8 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def OnBedDown(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z10.2 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def OnBedUp2(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def OnBedDown2(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z20 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def AllowNext(self):
		if self.GetParent().headOffsetCalibration is not None and int(profile.getMachineSetting('extruder_amount')) > 1:
			wx.wizard.WizardPageSimple.Chain(self, self.GetParent().headOffsetCalibration)
		return True

	def OnResume(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
		if self._wizardState == -1:
			wx.CallAfter(self.infoBox.SetInfo, _('Homing printer...'))
			wx.CallAfter(self.upButton.Enable, False)
			wx.CallAfter(self.downButton.Enable, False)
			wx.CallAfter(self.upButton2.Enable, False)
			wx.CallAfter(self.downButton2.Enable, False)
			self.comm.sendCommand('M105')
			self.comm.sendCommand('G28')
			self._wizardState = 1
		elif self._wizardState == 2:
			if profile.getMachineSetting('has_heated_bed') == 'True':
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to back center...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') / 2.0, profile.getMachineSettingFloat('machine_depth'), feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 3
			else:
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to back left corner...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (0, profile.getMachineSettingFloat('machine_depth'), feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 3
		elif self._wizardState == 4:
			if profile.getMachineSetting('has_heated_bed') == 'True':
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to front right corner...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') - 5.0, 5, feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 7
			else:
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to back right corner...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') - 5.0, profile.getMachineSettingFloat('machine_depth') - 25, feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 5
		elif self._wizardState == 6:
			wx.CallAfter(self.infoBox.SetBusy, _('Moving head to front right corner...'))
			self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') - 5.0, 20, feedTravel))
			self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
			self.comm.sendCommand('M400')
			self._wizardState = 7
		elif self._wizardState == 8:
			wx.CallAfter(self.infoBox.SetBusy, _('Heating up printer...'))
			self.comm.sendCommand('G1 Z15 F%d' % (feedZ))
			self.comm.sendCommand('M104 S%d' % (profile.getProfileSettingFloat('print_temperature')))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (0, 0, feedTravel))
			self._wizardState = 9
		elif self._wizardState == 10:
			self._wizardState = 11
			wx.CallAfter(self.infoBox.SetInfo, _('Printing a square on the printer bed at 0.3mm height.'))
			feedZ = profile.getProfileSettingFloat('print_speed') * 60
			feedPrint = profile.getProfileSettingFloat('print_speed') * 60
			feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
			w = profile.getMachineSettingFloat('machine_width') - 10
			d = profile.getMachineSettingFloat('machine_depth')
			filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
			filamentArea = math.pi * filamentRadius * filamentRadius
			ePerMM = (profile.calculateEdgeWidth() * 0.3) / filamentArea
			eValue = 0.0

			gcodeList = [
				'G1 Z2 F%d' % (feedZ),
				'G92 E0',
				'G1 X%d Y%d F%d' % (5, 5, feedTravel),
				'G1 Z0.3 F%d' % (feedZ)]
			eValue += 5.0
			gcodeList.append('G1 E%f F%d' % (eValue, profile.getProfileSettingFloat('retraction_speed') * 60))

			for i in xrange(0, 3):
				dist = 5.0 + 0.4 * float(i)
				eValue += (d - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (dist, d - dist, eValue, feedPrint))
				eValue += (w - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (w - dist, d - dist, eValue, feedPrint))
				eValue += (d - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (w - dist, dist, eValue, feedPrint))
				eValue += (w - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (dist, dist, eValue, feedPrint))

			gcodeList.append('M400')
			self.comm.printGCode(gcodeList)
		self.resumeButton.Enable(False)

	def mcLog(self, message):
		print 'Log:', message

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if self._wizardState == 1:
			self._wizardState = 2
			wx.CallAfter(self.infoBox.SetAttention, _('Adjust the front left screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 3:
			self._wizardState = 4
			if profile.getMachineSetting('has_heated_bed') == 'True':
				wx.CallAfter(self.infoBox.SetAttention, _('Adjust the back screw of your printer bed\nSo the nozzle just hits the bed.'))
			else:
				wx.CallAfter(self.infoBox.SetAttention, _('Adjust the back left screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 5:
			self._wizardState = 6
			wx.CallAfter(self.infoBox.SetAttention, _('Adjust the back right screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 7:
			self._wizardState = 8
			wx.CallAfter(self.infoBox.SetAttention, _('Adjust the front right screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 9:
			if temp[0] < profile.getProfileSettingFloat('print_temperature') - 5:
				wx.CallAfter(self.infoBox.SetInfo, _('Heating up printer: %d/%d') % (temp[0], profile.getProfileSettingFloat('print_temperature')))
			else:
				wx.CallAfter(self.infoBox.SetAttention, _('The printer is hot now. Please insert some PLA filament into the printer.'))
				wx.CallAfter(self.resumeButton.Enable, True)
				self._wizardState = 10

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			if self._wizardState == 0:
				wx.CallAfter(self.infoBox.SetAttention, _('Use the up/down buttons to move the bed and adjust your Z endstop.'))
				wx.CallAfter(self.upButton.Enable, True)
				wx.CallAfter(self.downButton.Enable, True)
				wx.CallAfter(self.upButton2.Enable, True)
				wx.CallAfter(self.downButton2.Enable, True)
				wx.CallAfter(self.resumeButton.Enable, True)
				self._wizardState = -1
			elif self._wizardState == 11 and not self.comm.isPrinting():
				self.comm.sendCommand('G1 Z15 F%d' % (profile.getProfileSettingFloat('print_speed') * 60))
				self.comm.sendCommand('G92 E0')
				self.comm.sendCommand('G1 E-10 F%d' % (profile.getProfileSettingFloat('retraction_speed') * 60))
				self.comm.sendCommand('M104 S0')
				wx.CallAfter(self.infoBox.SetInfo, _('Calibration finished.\nThe squares on the bed should slightly touch each other.'))
				wx.CallAfter(self.infoBox.SetReadyIndicator)
				wx.CallAfter(self.GetParent().FindWindowById(wx.ID_FORWARD).Enable)
				wx.CallAfter(self.connectButton.Enable, True)
				self._wizardState = 12
		elif self.comm.isError():
			wx.CallAfter(self.infoBox.SetError, _('Failed to establish connection with the printer.'), 'http://wiki.ultimaker.com/Cura:_Connection_problems')

	def mcMessage(self, message):
		pass

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass

class headOffsetCalibrationPage(InfoPage):
	def __init__(self, parent):
		super(headOffsetCalibrationPage, self).__init__(parent, "Printer head offset calibration")

		self.AddText(_('This wizard will help you in calibrating the printer head offsets of your dual extrusion machine'))
		self.AddSeperator()

		self.connectButton = self.AddButton(_('Connect to printer'))
		self.comm = None

		self.infoBox = self.AddInfoBox()
		self.textEntry = self.AddTextCtrl('')
		self.textEntry.Enable(False)
		self.resumeButton = self.AddButton(_('Resume'))
		self.resumeButton.Enable(False)

		self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connectButton)
		self.Bind(wx.EVT_BUTTON, self.OnResume, self.resumeButton)

	def AllowBack(self):
		return True

	def OnConnect(self, e = None):
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnConnect)
			return
		self.connectButton.Enable(False)
		self.comm = machineCom.MachineCom(callbackObject=self)
		self.infoBox.SetBusy(_('Connecting to machine.'))
		self._wizardState = 0

	def OnResume(self, e):
		if self._wizardState == 2:
			self._wizardState = 3
			wx.CallAfter(self.infoBox.SetBusy, _('Printing initial calibration cross'))

			w = profile.getMachineSettingFloat('machine_width')
			d = profile.getMachineSettingFloat('machine_depth')

			gcode = gcodeGenerator.gcodeGenerator()
			gcode.setExtrusionRate(profile.getProfileSettingFloat('nozzle_size') * 1.5, 0.2)
			gcode.setPrintSpeed(profile.getProfileSettingFloat('bottom_layer_speed'))
			gcode.addCmd('T0')
			gcode.addPrime(15)
			gcode.addCmd('T1')
			gcode.addPrime(15)

			gcode.addCmd('T0')
			gcode.addMove(w/2, 5)
			gcode.addMove(z=0.2)
			gcode.addPrime()
			gcode.addExtrude(w/2, d-5.0)
			gcode.addRetract()
			gcode.addMove(5, d/2)
			gcode.addPrime()
			gcode.addExtrude(w-5.0, d/2)
			gcode.addRetract(15)

			gcode.addCmd('T1')
			gcode.addMove(w/2, 5)
			gcode.addPrime()
			gcode.addExtrude(w/2, d-5.0)
			gcode.addRetract()
			gcode.addMove(5, d/2)
			gcode.addPrime()
			gcode.addExtrude(w-5.0, d/2)
			gcode.addRetract(15)
			gcode.addCmd('T0')

			gcode.addMove(z=25)
			gcode.addMove(0, 0)
			gcode.addCmd('M400')

			self.comm.printGCode(gcode.list())
			self.resumeButton.Enable(False)
		elif self._wizardState == 4:
			try:
				float(self.textEntry.GetValue())
			except ValueError:
				return
			profile.putPreference('extruder_offset_x1', self.textEntry.GetValue())
			self._wizardState = 5
			self.infoBox.SetAttention(_('Please measure the distance between the horizontal lines in millimeters.'))
			self.textEntry.SetValue('0.0')
			self.textEntry.Enable(True)
		elif self._wizardState == 5:
			try:
				float(self.textEntry.GetValue())
			except ValueError:
				return
			profile.putPreference('extruder_offset_y1', self.textEntry.GetValue())
			self._wizardState = 6
			self.infoBox.SetBusy(_('Printing the fine calibration lines.'))
			self.textEntry.SetValue('')
			self.textEntry.Enable(False)
			self.resumeButton.Enable(False)

			x = profile.getMachineSettingFloat('extruder_offset_x1')
			y = profile.getMachineSettingFloat('extruder_offset_y1')
			gcode = gcodeGenerator.gcodeGenerator()
			gcode.setExtrusionRate(profile.getProfileSettingFloat('nozzle_size') * 1.5, 0.2)
			gcode.setPrintSpeed(25)
			gcode.addHome()
			gcode.addCmd('T0')
			gcode.addMove(50, 40, 0.2)
			gcode.addPrime(15)
			for n in xrange(0, 10):
				gcode.addExtrude(50 + n * 10, 150)
				gcode.addExtrude(50 + n * 10 + 5, 150)
				gcode.addExtrude(50 + n * 10 + 5, 40)
				gcode.addExtrude(50 + n * 10 + 10, 40)
			gcode.addMove(40, 50)
			for n in xrange(0, 10):
				gcode.addExtrude(150, 50 + n * 10)
				gcode.addExtrude(150, 50 + n * 10 + 5)
				gcode.addExtrude(40, 50 + n * 10 + 5)
				gcode.addExtrude(40, 50 + n * 10 + 10)
			gcode.addRetract(15)

			gcode.addCmd('T1')
			gcode.addMove(50 - x, 30 - y, 0.2)
			gcode.addPrime(15)
			for n in xrange(0, 10):
				gcode.addExtrude(50 + n * 10.2 - 1.0 - x, 140 - y)
				gcode.addExtrude(50 + n * 10.2 - 1.0 + 5.1 - x, 140 - y)
				gcode.addExtrude(50 + n * 10.2 - 1.0 + 5.1 - x, 30 - y)
				gcode.addExtrude(50 + n * 10.2 - 1.0 + 10 - x, 30 - y)
			gcode.addMove(30 - x, 50 - y, 0.2)
			for n in xrange(0, 10):
				gcode.addExtrude(160 - x, 50 + n * 10.2 - 1.0 - y)
				gcode.addExtrude(160 - x, 50 + n * 10.2 - 1.0 + 5.1 - y)
				gcode.addExtrude(30 - x, 50 + n * 10.2 - 1.0 + 5.1 - y)
				gcode.addExtrude(30 - x, 50 + n * 10.2 - 1.0 + 10 - y)
			gcode.addRetract(15)
			gcode.addMove(z=15)
			gcode.addCmd('M400')
			gcode.addCmd('M104 T0 S0')
			gcode.addCmd('M104 T1 S0')
			self.comm.printGCode(gcode.list())
		elif self._wizardState == 7:
			try:
				n = int(self.textEntry.GetValue()) - 1
			except:
				return
			x = profile.getMachineSettingFloat('extruder_offset_x1')
			x += -1.0 + n * 0.1
			profile.putPreference('extruder_offset_x1', '%0.2f' % (x))
			self.infoBox.SetAttention(_('Which horizontal line number lays perfect on top of each other? Front most line is zero.'))
			self.textEntry.SetValue('10')
			self._wizardState = 8
		elif self._wizardState == 8:
			try:
				n = int(self.textEntry.GetValue()) - 1
			except:
				return
			y = profile.getMachineSettingFloat('extruder_offset_y1')
			y += -1.0 + n * 0.1
			profile.putPreference('extruder_offset_y1', '%0.2f' % (y))
			self.infoBox.SetInfo(_('Calibration finished. Offsets are: %s %s') % (profile.getMachineSettingFloat('extruder_offset_x1'), profile.getMachineSettingFloat('extruder_offset_y1')))
			self.infoBox.SetReadyIndicator()
			self._wizardState = 8
			self.comm.close()
			self.resumeButton.Enable(False)

	def mcLog(self, message):
		print 'Log:', message

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if self._wizardState == 1:
			if temp[0] >= 210 and temp[1] >= 210:
				self._wizardState = 2
				wx.CallAfter(self.infoBox.SetAttention, _('Please load both extruders with PLA.'))
				wx.CallAfter(self.resumeButton.Enable, True)
				wx.CallAfter(self.resumeButton.SetFocus)

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			if self._wizardState == 0:
				wx.CallAfter(self.infoBox.SetInfo, _('Homing printer and heating up both extruders.'))
				self.comm.sendCommand('M105')
				self.comm.sendCommand('M104 S220 T0')
				self.comm.sendCommand('M104 S220 T1')
				self.comm.sendCommand('G28')
				self.comm.sendCommand('G1 Z15 F%d' % (profile.getProfileSettingFloat('print_speed') * 60))
				self._wizardState = 1
			if not self.comm.isPrinting():
				if self._wizardState == 3:
					self._wizardState = 4
					wx.CallAfter(self.infoBox.SetAttention, _('Please measure the distance between the vertical lines in millimeters.'))
					wx.CallAfter(self.textEntry.SetValue, '0.0')
					wx.CallAfter(self.textEntry.Enable, True)
					wx.CallAfter(self.resumeButton.Enable, True)
					wx.CallAfter(self.resumeButton.SetFocus)
				elif self._wizardState == 6:
					self._wizardState = 7
					wx.CallAfter(self.infoBox.SetAttention, _('Which vertical line number lays perfect on top of each other? Leftmost line is zero.'))
					wx.CallAfter(self.textEntry.SetValue, '10')
					wx.CallAfter(self.textEntry.Enable, True)
					wx.CallAfter(self.resumeButton.Enable, True)
					wx.CallAfter(self.resumeButton.SetFocus)

		elif self.comm.isError():
			wx.CallAfter(self.infoBox.SetError, _('Failed to establish connection with the printer.'), 'http://wiki.ultimaker.com/Cura:_Connection_problems')

	def mcMessage(self, message):
		pass

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass

class bedLevelWizard(wx.wizard.Wizard):
	def __init__(self):
		super(bedLevelWizard, self).__init__(None, -1, _("Bed leveling wizard"))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.mainPage = bedLevelWizardMain(self)
		self.headOffsetCalibration = None

		self.FitToPage(self.mainPage)
		self.GetPageAreaSizer().Add(self.mainPage)

		self.RunWizard(self.mainPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()

class headOffsetWizard(wx.wizard.Wizard):
	def __init__(self):
		super(headOffsetWizard, self).__init__(None, -1, _("Head offset wizard"))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.mainPage = headOffsetCalibrationPage(self)

		self.FitToPage(self.mainPage)
		self.GetPageAreaSizer().Add(self.mainPage)

		self.RunWizard(self.mainPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()
