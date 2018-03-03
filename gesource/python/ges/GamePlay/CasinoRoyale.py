from GamePlay import GEScenario
from .Utils.GEPlayerTracker import GEPlayerTracker
import random
import GEPlayer, GEUtil, GEMPGameRules, GEGlobal

USING_API = GEGlobal.API_VERSION_1_2_0

	#	#	#	#	#	#	#	#
	#							#
	#     - CasinoRoyale  -     #
	#							#
	#	#	#	#	#	#	#	#	#
			#  						#
			#  Created by Euphonic  #
			#						#
		#	#	#	#	#	#	#	#  #  #
		# 								  #
		#  Made for GoldenEye:Source 5.0  #
		#								  #
		#	#	#	#	#	#	#	#  #  #

#	* / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *
CasinoRoyaleVersion = "^uCasino Royale Version ^l5.0.0"
#	* / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *

class Weapon( object ):
	"""Handles information about each available weapon"""
	
	def __init__( self, name, printName, ammoCount ):
			self.name = name
			self.printName = printName
			self.ammoCount = ammoCount

class CasinoRoyale(GEScenario):
	
	# Track player-related variables
	USED_SKIP = "Has Player Used Skip?"
	SWITCHING_TEAMS = "Is The Player Switching Teams?"
	
	def __init__(self):
		super(CasinoRoyale, self).__init__()
		
		weaponListSingleFire = [ Weapon("pp7", "PP7s", 50), Weapon("dd44", "DD44s", 50), Weapon("sniper_rifle", "Sniper Rifles", 75), Weapon("silver_pp7", "Silver PP7s", 25), Weapon("golden_pp7", "Golden PP7s", 10), Weapon("cmag", "Cougar Magnums", 25), Weapon("golden_gun", "Golden Guns", 10), Weapon("shotgun", "Shotguns", 20) ]
		weaponListAutomatic = [ Weapon("klobb", "Klobbs", 50), Weapon("zmg", "ZMGs", 50), Weapon("d5k", "D5Ks", 50), Weapon("rcp90", "RCP90s", 50), Weapon("phantom", "Phantoms", 50), Weapon("kf7", "KF7s", 75), Weapon("AR33", "AR33s", 75), Weapon("auto_shotgun", "Automatic Shotguns", 20) ]
		weaponListSpecial = [ Weapon("grenade", "Grenades", 3), Weapon("remotemine", "Remote Mines", 3), Weapon("grenade_launcher", "Grenade Launchers", 4), Weapon("rocket_launcher", "Rocket Launchers", 2), Weapon("knife_throwing", "Throwing Knives", 5), Weapon("moonraker", "Moonraker Lasers", 0), Weapon("knife", "Hunting Knives", 0)]
		
		self.weaponList = [weaponListSingleFire, weaponListAutomatic, weaponListSpecial]
	
		# Defines new variable that will track the current weapon, when created it's outside of the weaponlist length
		self.weaponIndex = [-1, -1]
		# Length of each weapon round
		self.timerMax = 40 * 10
		# Current weapon timer
		self.weaponTimer = self.timerMax
		# Creates player tracker
		self.playerTracker = GEPlayerTracker( self )
		# Defines a toggle that says if round is active or not
		self.isRoundActive = False
		# Next two keep track of how many kills that team has had during the current weapon round
		self.roundScoreJanus = 0
		self.roundScoreMI6 = 0
		
		self.skipTextColor = GEUtil.CColor(232,180,2,240)
		self.skipTextFadedColor = GEUtil.CColor(232,180,2,10)
		self.timerBarColor = GEUtil.CColor(220,220,220,240)
		
		self.skipMsgColor = GEUtil.CColor(232,180,2,230)
		self.weaponMsgColor = GEUtil.CColor(220,220,220,240)
		
		self.timerBarIndex = 0
		self.skipTextIndex = 1
		
		self.scoreDisplayChannel = 0
		self.skipMSgChannel = 1
		self.weaponMsgChannel = 2
		
		self.skipTextYPos = 0.67
		self.weaponMsgYPos = 0.71
		
		self.winMsgJanus = "^rJanus ^1scored the most kills and ^ugot a point"
		self.winMsgMI6 = "^iMI6 ^1scored the most kills and ^ugot a point"
		self.winMsgTie = "^1Tie score! Both teams ^ugot a point"

	def CanPlayerHaveItem( self, player, item ):
		newItem = item.GetClassname()
		currentWeapon = self.weaponList[ self.weaponIndex[0] ][ self.weaponIndex[1] ]
		
		if newItem == "weapon_" + currentWeapon.name or newItem == "weapon_slappers" or item.GetClassname().startswith("item_armorvest") or item.GetClassname().startswith("ge_ammo"):
			return True

		else:
			return False
	
	def CanPlayerHaveWeapon(self, player, weapon ):		
		if not self.playerTracker.GetValue( player, self.WEAPON_GIVEN ):
			return True
		
		if not weapon or not player:
			return False
		else:
			currentWeaponName = self.weaponList[ self.weaponIndex[0] ][ self.weaponIndex[1] ].name
			newWeaponName = weapon.GetClassname().replace("weapon_", "").lower()
			
			if newWeaponName == currentWeaponName or newWeaponName == "slappers":
				return True
			else:
				return False
	
	def OnPlayerSpawn(self, player):
		self.playerTracker.SetValue( player, self.SWITCHING_TEAMS, False )
		self.showTimerBar(player)
		if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
			self.showRoundScore(player)
		if int(GEUtil.GetCVarValue("cr_skip")):
				self.showSkipText(player)
		self.giveWeapons(player)
		
	def OnPlayerConnect(self, player):
		if self.checkFreeSkip():
			self.playerTracker.SetValue( player, self.USED_SKIP, False )
		else:
			self.playerTracker.SetValue( player, self.USED_SKIP, True )

	def OnRoundBegin(self):
		self.isRoundActive = True
		GEMPGameRules.ResetAllPlayersScores()
		GEMPGameRules.DisableWeaponSpawns()
		self.weaponTimer = self.timerMax
		self.generateIndex()
		self.resetRoundScore()
		GEMPGameRules.ResetAllPlayersScores()
		if self.checkFreeSkip():
			self.updateSkips()
		else:
			for i in range(32):
				if not GEPlayer.IsValidPlayerIndex(i):
					continue
				player = GEPlayer.GetMPPlayer(i)
				self.playerTracker.SetValue( player, self.USED_SKIP, True )

	def OnRoundEnd(self):
		self.isRoundActive = False
		GEUtil.ServerCommand("ge_weaponset moonraker_arena")
		if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
			self.awardRoundScore()
			self.hideRoundScore(None)
	
	def OnThink(self):
		self.weaponTimer -= 1
		if self.weaponTimer >= 0:
			GEUtil.UpdateHudProgressBar(None, self.timerBarIndex, float(self.weaponTimer))
		# If less than zero, the timer has ended and everyone needs a new index. If team scoring, tab scores
		if self.weaponTimer <= 0:
			self.weaponTimer = self.timerMax
			if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
				self.awardRoundScore()
			self.generateIndex()
			self.updatePlayers()

	def CanPlayerChangeTeam( self, player, oldteam, newteam, wasforced ):
		# This helps tell the difference between suicide by switching teams and suicide by gameplay
		if player and oldteam != GEGlobal.TEAM_SPECTATOR and newteam != GEGlobal.TEAM_SPECTATOR:
			if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
				self.playerTracker.SetValue( player, self.SWITCHING_TEAMS, True )
		return True

	def OnCVarChanged(self, name, oldvalue, newvalue):
		if name == "cr_timer":
			GEUtil.RemoveHudProgressBar(None, self.timerBarIndex)
			self.timerMax = float(newvalue) * 10
			if self.weaponTimer >= float(newvalue):
				self.weaponTimer = float(newvalue)
			self.showTimerBar(None)

		if name == "cr_teamscoring" and GEMPGameRules.IsTeamplay():
			if int(newvalue) == 0 and int(oldvalue) == 1:
				GEMPGameRules.ResetAllTeamsScores()
				self.resetRoundScore()
				GEMPGameRules.EndRound(False)
				GEUtil.HudMessage( None, "", 0.0, 0.0, GEUtil.CColor(255,255,255,255), 0, self.scoreDisplayChannel )
			elif float(newvalue) == 1 and float(oldvalue) == 0:
				GEMPGameRules.ResetAllTeamsScores()
				self.resetRoundScore()
				GEMPGameRules.EndRound(False)
				self.showRoundScore(None)
				
		elif name == "cr_skip":
			if int(GEUtil.GetCVarValue("cr_skip")) == 0:
				for i in range(32):
					if not GEPlayer.IsValidPlayerIndex(i):
						continue
					player = GEPlayer.GetMPPlayer(i)
					GEUtil.RemoveHudProgressBar(player, self.skipTextIndex)
			else:
				for i in range(32):
					if not GEPlayer.IsValidPlayerIndex(i):
						continue
					player = GEPlayer.GetMPPlayer(i)
					if self.checkFreeSkip():
						self.playerTracker.SetValue( player, self.USED_SKIP, False )
					self.showSkipText(player)
	
		elif name == "ge_teamplay" and newvalue == 0:
			self.hideRoundScore(None)
			
	def OnPlayerSay(self, player, text):
		if text == "!version":
			GEUtil.ClientPrint(player, GEGlobal.HUD_PRINTTALK, CasinoRoyaleVersion)

		elif text == "!voodoo" and int(GEUtil.GetCVarValue("cr_skip")):
			if self.playerTracker.GetValue( player, self.USED_SKIP):
				GEUtil.PlaySoundToPlayer( player, "Buttons.beep_denied", False )
			else:
				if self.isRoundActive and player.GetTeamNumber() != GEGlobal.TEAM_SPECTATOR:
					GEUtil.EmitGameplayEvent( "cr_skipused", "%i" % player.GetUserID() )
					name = player.GetPlayerName()
					GEUtil.HudMessage( None, name + " skipped to the next weapon!", -1, self.skipTextYPos, self.skipMsgColor, 3.0, self.skipMSgChannel )
					self.playerTracker.SetValue( player, self.USED_SKIP, True)
					self.showSkipText(player)
					self.weaponTimer = 0
			return True
			
		return False
		
	def GetPrintName(self):
		return "Casino Royale"
		
	def GetScenarioHelp( self, help_obj ):
		help_obj.SetDescription( "Better stay alert in this constantly evolving gamemode!\n\nAll players carry the same weapon. Every time the counter depletes, a new weapon will be randomly selected and the chaos continues!\n\nOnce per round, press your '!voodoo' key to skip to the next weapon. Melee kills restore this ability. Change your !voodoo key under Keyboard Options.\n\nTeamplay: Toggleable\n\nCreated by Euphonic" )
		
	def GetGameDescription(self):
		if GEMPGameRules.IsTeamplay():
			return "Team Casino Royale"
		else:
			return "Casino Royale"
		
	def GetTeamPlay(self):
		return GEGlobal.TEAMPLAY_TOGGLE
		
	def OnLoadGamePlay(self):
		GEUtil.PrecacheSound("GEGamePlay.Token_Drop_Enemy")
		GEUtil.PrecacheSound("GEGamePlay.Token_Chime")
		GEUtil.PrecacheSound("Buttons.beep_denied")
		self.CreateCVar("cr_timer", str(int(self.timerMax) / 10), "Amount of time (in seconds) between weapon switches")
		self.CreateCVar("cr_skip", "1", "Enable players to use their 'skip' to switch to next weapon immediately")
		self.CreateCVar("cr_free_skip", "1", "0 never starts players with a skip, 1 only when not teamplay or when teamscoring is off, 2 always gives a skip")
		self.CreateCVar("cr_teamscoring", "1", "When enabled, team scoring is the number of weapon 'rounds' in which that team had the most kills; changing from 0 to 1 restarts the round")
		GEMPGameRules.SetAllowTeamSpawns( False )
		GEMPGameRules.GetTokenMgr().SetGlobalAmmo( "weapon_moonraker", 0 )	# Fixes glitch where hunting knives cause ammo spawns not to function
		GEUtil.ServerCommand("ge_weaponset moonraker_arena")

	def OnPlayerKilled(self, victim, killer, weapon):
		#what exactly got killed?
		if not victim:
			return

		#death by world
		if not killer:
			victim.IncrementScore( -1 )
			if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
				team = victim.GetTeamNumber()
				if team == GEGlobal.TEAM_MI6:
					self.addRoundScore(GEGlobal.TEAM_MI6, -1)
				elif team == GEGlobal.TEAM_JANUS:
					self.addRoundScore(GEGlobal.TEAM_JANUS, -1)
			return
		
		if int(GEUtil.GetCVarValue("cr_skip")) != 0:
			weaponName = weapon.GetClassname().replace('weapon_', '').lower()
			if weaponName == "knife" or weaponName == "slappers":
				self.giveSkip(killer)
				
		if victim.GetIndex() == killer.GetIndex():
			killer.IncrementScore( -1 )
			if not self.playerTracker.GetValue(killer, self.SWITCHING_TEAMS):
				if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
					team = killer.GetTeamNumber()
					if team == GEGlobal.TEAM_MI6 or GEGlobal.TEAM_JANUS:
						self.addRoundScore(team, -1)
			
		elif GEMPGameRules.IsTeamplay() and killer.GetTeamNumber() == victim.GetTeamNumber():
			killer.IncrementScore( -1 )
			if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
				team = killer.GetTeamNumber()
				if team == GEGlobal.TEAM_MI6 or GEGlobal.TEAM_JANUS:
					self.addRoundScore(team, -1)
		else:
			killer.IncrementScore( 1 )
			if GEMPGameRules.IsTeamplay() and int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
				team = killer.GetTeamNumber()
				if team == GEGlobal.TEAM_MI6 or GEGlobal.TEAM_JANUS:
					self.addRoundScore(team, 1)
			else:
				team = GEMPGameRules.GetTeam(killer.GetTeamNumber())
				team.IncrementRoundScore( 1 )


			####################					# # # # # # # # # # # # # # # # # #					   ####################
			#########################################         Custom Functions        #########################################
			####################					# # # # # # # # # # # # # # # # # #					   ####################

				
	def generateIndex(self):
		oldIndex = self.weaponIndex
		newIndex = [ -1, -1 ]
		
		groupOptions = []
		if len(self.weaponList) != 1:
			for n in range(0, len(self.weaponList)):
				groupOptions += [n]
				if n != oldIndex[0]:
					groupOptions += [n]
			newIndex[0] = random.choice(groupOptions)
		else:
			newIndex[0] = 0

		weaponOptions = list(range(0, len(self.weaponList[newIndex[0]])))
		if newIndex[0] == oldIndex[0]:
			weaponOptions.pop(oldIndex[1])
		newIndex[1] = random.choice(weaponOptions)

		self.weaponIndex = newIndex
		
		#Remove global ammo spawns
		if oldIndex[0] != -1:
			oldWeapon = self.weaponList[ oldIndex[0] ][ oldIndex[1] ]
			if not oldWeapon.name == "knife" and not oldWeapon.name == "moonraker":
				GEMPGameRules.GetTokenMgr().RemoveGlobalAmmo( "weapon_" + oldWeapon.name)
		
		#Set global ammo spawns
		newWeapon = self.weaponList[ newIndex[0] ][ newIndex[1] ]
		if not newWeapon.name == "knife" and not newWeapon.name == "moonraker":
			GEMPGameRules.GetTokenMgr().SetGlobalAmmo( "weapon_" + newWeapon.name, newWeapon.ammoCount )
	
	def updatePlayers(self):
		GEUtil.EmitGameplayEvent( "cr_weaponchange" )
		
		newWeapon = self.weaponList[ self.weaponIndex[0] ][ self.weaponIndex[1] ]
		GEUtil.HudMessage( None, "New Weapon: " + newWeapon.printName , -1, self.weaponMsgYPos, self.weaponMsgColor, 3.0, self.weaponMsgChannel )
		
		for i in range(32):
			if not GEPlayer.IsValidPlayerIndex(i):
				continue
			player = GEPlayer.GetMPPlayer(i)
			GEUtil.PlaySoundToPlayer( player, "GEGamePlay.Token_Drop_Enemy", True )
			if player.GetTeamNumber() != GEGlobal.TEAM_SPECTATOR:
				self.giveWeapons(player)

	def updateSkips(self):
		if int(GEUtil.GetCVarValue("cr_skip")):
			for i in range(32):
				if not GEPlayer.IsValidPlayerIndex(i):
					continue
				player = GEPlayer.GetMPPlayer(i)
				self.playerTracker.SetValue( player, self.USED_SKIP, False )
				self.showSkipText(player)
	
	def giveSkip(self, player):
		if self.playerTracker.GetValue(player, self.USED_SKIP):
			self.playerTracker.SetValue(player, self.USED_SKIP, False )
			GEUtil.EmitGameplayEvent( "cr_restoredskip", "%i" % player.GetUserID() )
			GEUtil.PlaySoundToPlayer( player, "GEGamePlay.Token_Chime", True )
			self.showSkipText(player)
	
	def giveWeapons(self, player):
		player.StripAllWeapons()
		player.GiveNamedWeapon("weapon_slappers", 1)
		newWeapon = self.weaponList[ self.weaponIndex[0] ][ self.weaponIndex[1] ]
		player.GiveNamedWeapon( "weapon_" + newWeapon.name, newWeapon.ammoCount )
		player.WeaponSwitch( "weapon_" + newWeapon.name )

	def addRoundScore(self, team, amount):
		if int(GEUtil.GetCVarValue("cr_teamscoring")) == 1:
			if team == GEGlobal.TEAM_MI6:
				self.roundScoreMI6 += amount
			if team == GEGlobal.TEAM_JANUS:
				self.roundScoreJanus += amount

			self.showRoundScore(None)

	def resetRoundScore(self):
		self.roundScoreMI6 = 0; self.roundScoreJanus = 0
		self.showRoundScore(None)

	def showRoundScore(self, target):
		GEUtil.HudMessage( target, "^r" + str(self.roundScoreJanus) + "    ^w:    ^c" + str(self.roundScoreMI6), -1, 0.0, GEUtil.CColor(255,255,255,255), float('inf'), self.scoreDisplayChannel )

	def hideRoundScore(self, target):
		GEUtil.HudMessage( target, "", -1, 0.0, GEUtil.CColor(255,255,255,255), 0, self.scoreDisplayChannel )

	def awardRoundScore(self):
		# For non-zero ties, award both teams a point
		if self.roundScoreMI6 == self.roundScoreJanus and not self.roundScoreJanus == 0:
			GEUtil.PostDeathMessage( self.winMsgTie )
			GEMPGameRules.GetTeam(GEGlobal.TEAM_MI6).IncrementRoundScore( 1 )
			GEMPGameRules.GetTeam(GEGlobal.TEAM_JANUS).IncrementRoundScore( 1 )
			GEUtil.EmitGameplayEvent( "cr_team_tie", str(GEGlobal.TEAM_MI6), str(GEGlobal.TEAM_JANUS) )
		
		elif self.roundScoreMI6 > self.roundScoreJanus:
			GEUtil.PostDeathMessage( self.winMsgMI6 )
			GEMPGameRules.GetTeam(GEGlobal.TEAM_MI6).IncrementRoundScore( 1 )
			GEUtil.EmitGameplayEvent( "cr_team_win", str(GEGlobal.TEAM_MI6) )
			GEUtil.EmitGameplayEvent( "cr_team_lose", str(GEGlobal.TEAM_JANUS) )
		
		elif self.roundScoreMI6 < self.roundScoreJanus:
			GEUtil.PostDeathMessage( self.winMsgJanus )
			GEMPGameRules.GetTeam(GEGlobal.TEAM_JANUS).IncrementRoundScore( 1 )
			GEUtil.EmitGameplayEvent( "cr_team_win", str(GEGlobal.TEAM_JANUS) )
			GEUtil.EmitGameplayEvent( "cr_team_lose", str(GEGlobal.TEAM_MI6) )

		self.resetRoundScore()

	def showTimerBar(self, target):
		GEUtil.InitHudProgressBar(target, self.timerBarIndex, "Next\nWeapon", 1, float(self.timerMax), -1, .04, 130, 12, self.timerBarColor )

	def showSkipText(self, target):
		if not self.playerTracker.GetValue( target, self.USED_SKIP):
			GEUtil.InitHudProgressBar(target, self.skipTextIndex, "[SKIP]", 0, float(self.timerMax), .59, .03, 35, 10, self.skipTextColor )
		else:
			GEUtil.InitHudProgressBar(target, self.skipTextIndex, "[SKIP]", 0, float(self.timerMax), .59, .03, 35, 10, self.skipTextFadedColor )

	def checkFreeSkip(self):
		if int(GEUtil.GetCVarValue("cr_free_skip")) == 2:
			return True
		elif int(GEUtil.GetCVarValue("cr_free_skip")) == 1 and (not int(GEUtil.GetCVarValue("cr_teamscoring")) or not GEMPGameRules.IsTeamplay()):
			return True
		else:
			return False