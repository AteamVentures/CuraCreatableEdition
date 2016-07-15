__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import os
import webbrowser
from wx.lib import scrolledpanel

from Cura.util import profile
from Cura.util import pluginInfo
from Cura.util import explorer

class ListBoxEnh(wx.ListBox):
	def GetValue(self):
		return wx.ListBox.GetSelection(self)

class pluginPanel(wx.Panel):
	def __init__(self, parent, callback):
		wx.Panel.__init__(self, parent,-1)
		#Plugin page
		self.pluginList = pluginInfo.getPluginList("postprocess")
		self.callback = callback

		sizer = wx.GridBagSizer(2, 2)
		self.SetSizer(sizer)

		pluginStringList = []
		for p in self.pluginList:
			pluginStringList.append(p.getName())

		self.listbox = wx.ListBox(self, -1, choices=pluginStringList)
		title = wx.StaticText(self, -1, _("Plugins:"))
		title.SetFont(wx.Font(wx.SystemSettings.GetFont(wx.SYS_ANSI_VAR_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
		helpButton = wx.Button(self, -1, '?', style=wx.BU_EXACTFIT)
		addButton = wx.Button(self, -1, 'V', style=wx.BU_EXACTFIT)
		openPluginLocationButton = wx.Button(self, -1, _("Open plugin location"))
		sb = wx.StaticBox(self, label=_("Enabled plugins"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.pluginEnabledPanel = scrolledpanel.ScrolledPanel(self)
		self.pluginEnabledPanel.SetupScrolling(False, True)

		sizer.Add(title, (0,0), border=10, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.TOP)
		sizer.Add(helpButton, (0,1), border=10, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.TOP)
		sizer.Add(self.listbox, (1,0), span=(2,2), border=10, flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
		sizer.Add(addButton, (3,0), span=(1,2), border=5, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM)
		sizer.Add(boxsizer, (4,0), span=(4,2), border=10, flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
		sizer.Add(openPluginLocationButton, (8, 0), border=10, flag=wx.LEFT|wx.BOTTOM)
		boxsizer.Add(self.pluginEnabledPanel, 1, flag=wx.EXPAND)

		sizer.AddGrowableCol(0)
		sizer.AddGrowableRow(1) # Plugins list box
		sizer.AddGrowableRow(4) # Enabled plugins
		sizer.AddGrowableRow(5) # Enabled plugins
		sizer.AddGrowableRow(6) # Enabled plugins

		sizer = wx.BoxSizer(wx.VERTICAL)
		self.pluginEnabledPanel.SetSizer(sizer)

		self.Bind(wx.EVT_BUTTON, self.OnAdd, addButton)
		self.Bind(wx.EVT_BUTTON, self.OnGeneralHelp, helpButton)
		self.Bind(wx.EVT_BUTTON, self.OnOpenPluginLocation, openPluginLocationButton)
		self.listbox.Bind(wx.EVT_LEFT_DCLICK, self.OnAdd)
		self.panelList = []
		self.updateProfileToControls()

	def updateProfileToControls(self):
		self.pluginConfig = pluginInfo.getPostProcessPluginConfig()
		for p in self.panelList:
			p.Show(False)
			self.pluginEnabledPanel.GetSizer().Detach(p)
		self.panelList = []
		for pluginConfig in self.pluginConfig:
			self._buildPluginPanel(pluginConfig)

	def _buildPluginPanel(self, pluginConfig):
		plugin = None
		for pluginTest in self.pluginList:
			if pluginTest.getFilename() == pluginConfig['filename']:
				plugin = pluginTest
		if plugin is None:
			return False

		pluginPanel = wx.Panel(self.pluginEnabledPanel)
		s = wx.GridBagSizer(2, 2)
		pluginPanel.SetSizer(s)
		title = wx.StaticText(pluginPanel, -1, plugin.getName())
		title.SetFont(wx.Font(wx.SystemSettings.GetFont(wx.SYS_ANSI_VAR_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
		remButton = wx.Button(pluginPanel, -1, 'X', style=wx.BU_EXACTFIT)
		helpButton = wx.Button(pluginPanel, -1, '?', style=wx.BU_EXACTFIT)
		s.Add(title, pos=(0,1), span=(1,2), flag=wx.ALIGN_BOTTOM|wx.TOP|wx.LEFT|wx.RIGHT, border=5)
		s.Add(helpButton, pos=(0,0), span=(1,1), flag=wx.TOP|wx.LEFT|wx.ALIGN_RIGHT, border=5)
		s.Add(remButton, pos=(0,3), span=(1,1), flag=wx.TOP|wx.RIGHT|wx.ALIGN_RIGHT, border=5)
		s.Add(wx.StaticLine(pluginPanel), pos=(1,0), span=(1,4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=3)
		info = wx.StaticText(pluginPanel, -1, plugin.getInfo())
		info.Wrap(300)
		s.Add(info, pos=(2,0), span=(1,4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=3)

		pluginPanel.paramCtrls = {}
		i = 0
		for param in plugin.getParams():
			if param['type'].lower() == 'bool': #check for type bool in plugin
				if param['default'].lower() in ["true","false"]:
					value = param['default'].lower()=="true" #sets default 'true'
				else:
					value = int(param['default'])
			elif param['type'].lower() == 'list': #check for 'type' list in plugin
				ListOfItems = param['default'].split(',') #prepares selection entries
				value = 0 #sets default selection first entry
			else:
				value = param['default']
			if param['name'] in pluginConfig['params']:
				value = pluginConfig['params'][param['name']]
			s.Add(wx.StaticText(pluginPanel, -1, param['description']), pos=(3+i,0), span=(1,2), flag=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL,border=3)
			if param['type'].lower() == 'bool': #checks for type boolean, displays checkbox and sets stored value
				ctrl = wx.CheckBox(pluginPanel, -1, "")
				ctrl.SetValue(value in {"TRUE",True,1})
				s.Add(ctrl, pos=(3+i,2), span=(1,2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=3)
				ctrl.Bind(wx.EVT_CHECKBOX, self.OnSettingChange) #bind the checkbox event to the same method as for the standard text boxes
			elif param['type'].lower() == 'list': #checks for 'type' list, displays listbox and sets stored value (integer)
				ctrl = ListBoxEnh(pluginPanel, -1, wx.DefaultPosition, (-1,(wx.SystemSettings.GetFont(wx.SYS_ANSI_VAR_FONT).GetPixelSize()[1]+1)*len(ListOfItems)+6), ListOfItems)
				ctrl.Select(value)
				s.Add(ctrl, pos=(3+i,2), span=(1,2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=3)
				ctrl.Bind(wx.EVT_LISTBOX, self.OnSettingChange) #bind the listbox event to the same method as for the standard text boxes (derived class necessary due to usage of SetValue method)
			else: #standard text box
				ctrl = wx.TextCtrl(pluginPanel, -1, value)
				s.Add(ctrl, pos=(3+i,2), span=(1,2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=3)
				ctrl.Bind(wx.EVT_TEXT, self.OnSettingChange)

			pluginPanel.paramCtrls[param['name']] = ctrl

			i += 1
		s.Add(wx.StaticLine(pluginPanel), pos=(3+i,0), span=(1,4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT,border=3)

		self.Bind(wx.EVT_BUTTON, self.OnRem, remButton)
		self.Bind(wx.EVT_BUTTON, self.OnHelp, helpButton)

		s.AddGrowableCol(1)
		pluginPanel.SetBackgroundColour(self.GetParent().GetBackgroundColour())
		self.pluginEnabledPanel.GetSizer().Add(pluginPanel, flag=wx.EXPAND)
		self.pluginEnabledPanel.Layout()
		self.pluginEnabledPanel.SetSize((1,1))
		self.Layout()
		self.pluginEnabledPanel.ScrollChildIntoView(pluginPanel)
		self.panelList.append(pluginPanel)
		return True

	def OnSettingChange(self, e):
		for panel in self.panelList:
			idx = self.panelList.index(panel)
			for k in panel.paramCtrls.keys():
				if type(panel.paramCtrls[k].GetValue()) == bool:
					self.pluginConfig[idx]['params'][k] = int(panel.paramCtrls[k].GetValue())
				else:
					self.pluginConfig[idx]['params'][k] = panel.paramCtrls[k].GetValue()
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()

	def OnAdd(self, e):
		if self.listbox.GetSelection() < 0:
			wx.MessageBox(_("You need to select a plugin before you can add anything."), _("Error: no plugin selected"), wx.OK | wx.ICON_INFORMATION)
			return
		p = self.pluginList[self.listbox.GetSelection()]
		newConfig = {'filename': p.getFilename(), 'params': {}}
		if not self._buildPluginPanel(newConfig):
			return
		self.pluginConfig.append(newConfig)
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()

	def OnRem(self, e):
		panel = e.GetEventObject().GetParent()
		sizer = self.pluginEnabledPanel.GetSizer()
		idx = self.panelList.index(panel)

		panel.Show(False)
		for p in self.panelList:
			sizer.Detach(p)
		self.panelList.pop(idx)
		for p in self.panelList:
				sizer.Add(p, flag=wx.EXPAND)

		self.pluginEnabledPanel.Layout()
		self.pluginEnabledPanel.SetSize((1,1))
		self.Layout()

		self.pluginConfig.pop(idx)
		pluginInfo.setPostProcessPluginConfig(self.pluginConfig)
		self.callback()

	def OnHelp(self, e):
		panel = e.GetEventObject().GetParent()
		idx = self.panelList.index(panel)

		fname = self.pluginConfig[idx]['filename'].lower()
		fname = fname[0].upper() + fname[1:]
		fname = fname[:fname.rfind('.')]
		webbrowser.open('http://wiki.ultimaker.com/CuraPlugin:_' + fname)

	def OnGeneralHelp(self, e):
		webbrowser.open('http://wiki.ultimaker.com/Category:CuraPlugin')

	def OnOpenPluginLocation(self, e):
		if not os.path.exists(pluginInfo.getPluginBasePaths()[0]):
			os.mkdir(pluginInfo.getPluginBasePaths()[0])
		explorer.openExplorerPath(pluginInfo.getPluginBasePaths()[0])

	def GetActivePluginCount(self):
		pluginCount = 0
		for pluginConfig in self.pluginConfig:
			self._buildPluginPanel(pluginConfig)

			for pluginTest in self.pluginList:
				if pluginTest.getFilename() == pluginConfig['filename']:
					pluginCount += 1

		return pluginCount