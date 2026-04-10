# Zen Macro (MacOS)
# sleepytil, 2025-2026

import customtkinter
import os
import discord_webhook
import json
import datetime
import psutil
import sys
import time
import configparser
import platformdirs
import subprocess
import requests
import logging
import pyautogui
import webbrowser
from PIL import Image
from pathlib import Path

class macroActivity(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # Logging
        logging.basicConfig(
            filename='crash.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'  # Customize the log format
        )

        self.logger = logging.getLogger('mylogger')

        # Variables > Read Config
        self.ROOT_DIR = Path.home() / "Documents" / "Zen Macro Data"
        self.config_name = 'config.ini'
        self.ROOT_DIR.mkdir(parents=True, exist_ok=True)
        self.config_path = self.ROOT_DIR / self.config_name
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            self.logger.info("Config file not found, creating one...")
            print("[DEBUG] Config file not found, creating one...")
            self.config['Webhook'] = {'webhook_url': "", 'private_server': "",  'multi_webhook': "0", 'multi_webhook_urls': "", 'discord_user_id': ""}
            self.config['Macro'] = {'aura_detection': "0", 'last_roblox_version': "", 'aura_min_rarity': "", 'anti_afk': "0"}
            self.config['Stats'] = {'total_biomes_discovered': "0"}
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)
        self.config.read(self.config_path)
        self.webhookURL = customtkinter.StringVar(self, self.config['Webhook']['webhook_url'])
        self.psURL = customtkinter.StringVar(self, self.config['Webhook']['private_server'])
        self.totalBiomesFound = int(self.config['Stats']['total_biomes_discovered'])
        self.userID = None
        try:
            self.userID = customtkinter.StringVar(self, self.config['Webhook']['discord_user_id'])
        except Exception as e:
            print(f"Error: No Discord User ID found in config, skipping...\nDebug: {e}")
            self.userID = customtkinter.StringVar(self, "")
            self.write_config()
            pass
        self.multi_webhook = customtkinter.StringVar(self, self.config['Webhook']['multi_webhook'])
        self.aura_detection = customtkinter.IntVar(self, int(self.config['Macro']['aura_detection']))
        self.auraMin = None
        try:
            self.auraMin = customtkinter.StringVar(self, self.config['Macro']['aura_min_rarity'])
        except Exception as e:
            print(f"Error: No Minimum Aura Rarity found in config, skipping...\nDebug: {e}")
            self.auraMin = customtkinter.StringVar(self, "")
            self.write_config()
            pass
        self.anti_afk = 0
        try:
            self.anti_afk = customtkinter.IntVar(self, int(self.config['Macro']['anti_afk']))
        except Exception as e:
            print(f"Error: No Anti-AFK setting found in config, skipping...\nDebug: {e}")
            self.anti_afk = customtkinter.IntVar(self, 0)
            self.write_config()
            pass
        webhook_urls_string = customtkinter.StringVar(self, self.config['Webhook']['multi_webhook_urls'])
        self.webhook_urls = webhook_urls_string.get().split()
        self.auraRarities = self.loadAuraInfo()

        # Variables
        self.started = False
        self.roblox_open = False
        self.destroyed = False
        self.stopped = False
        self.paused = False
        self.destroyed = False
        self.macro_start_time = 0
        self.log_directory = platformdirs.user_log_dir("Roblox", None)

        self.biome_times = {
            "SAND STORM": 650,
            "HELL": 666,
            "STARFALL": 650,
            "CORRUPTION": 650,
            "NULL": 99,
            "WINDY": 120,
            "RAINY": 120,
            "SNOWY": 120,
            "HEAVEN": 240,
            "GLITCHED": 164,
            "DREAMSPACE": 192,
            "CYBERSPACE": 720,
            "AURORA": 300,
            "EGGLAND": 0
        }

        self.biome_colours = {
            "NORMAL": "FFFFFF",
            "SAND STORM": "F4C27C",
            "HELL": "5C1219",
            "STARFALL": "6784E0",
            "CORRUPTION": "9042FF",
            "NULL": "000000",
            "WINDY": "91F7FF",
            "RAINY": "4385FF",
            "SNOWY": "C4F5F6",
            "HEAVEN": "FFEE8C",
            "GLITCHED": "65FF65",
            "DREAMSPACE": "FF7DFF",
            "CYBERSPACE": "03045E",
            "AURORA": "C1C3F9",
            "EGGLAND": "BAFFD0"
        }

        # UI
        customtkinter.set_default_color_theme("blue")
        self.title("Zen")
        self.geometry("720x500")
        self.resizable(False, False)
        tabview = customtkinter.CTkTabview(self, width=720, height=440)
        tabview.grid(row=0, column=0, sticky='nsew', columnspan=75)
        tabview.add("Home")
        tabview.add("Webhook")
        tabview.add("Config")
        tabview.add("Stats")
        tabview.add("Credits")
        tabview.set("Home")
        tabview._segmented_button.configure(font=customtkinter.CTkFont(family="Segoe UI", size=16))
        tabview._segmented_button.grid(sticky="w", padx=15)
        updateInfo = customtkinter.CTkTextbox(tabview.tab("Home"), width=707, height=360, corner_radius=0)
        updateInfo.grid(row=0, column=0, sticky="nsew")
        updateInfo.insert("0.0", self.load_notice_tab())
        updateInfo.configure(state="disabled")
        start_button = customtkinter.CTkButton(self, text="Start",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=self.startMacro)
        start_button.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

        stop_button = customtkinter.CTkButton(self, text="Stop",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=self.stop)
        stop_button.grid(row=1, column=1, padx=(10, 0), pady=(10, 0), sticky="w")

        version_label = customtkinter.CTkLabel(tabview.tab("Home"), text="Build 2.2", font=customtkinter.CTkFont(family="Segoe UI", size=14, weight="bold"))
        version_label.grid(row=1, column=0, padx=(5, 0), sticky="nw")

        self.state_label = customtkinter.CTkLabel(tabview.tab("Home"), text="Macro Stopped", font=customtkinter.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.state_label.grid(row=1, column=0, padx=(0, 5), sticky="ne")

        til_pfp = customtkinter.CTkImage(dark_image=Image.open("sleepytil.png"), size=(100, 100))
        til_pfp_label = customtkinter.CTkLabel(tabview.tab("Credits"), image=til_pfp, text="")
        til_pfp_label.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

        credits_frame = customtkinter.CTkFrame(tabview.tab("Credits"))
        credits_frame.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="w")
        dev_label = customtkinter.CTkLabel(credits_frame, text="sleepytil - Creator", font=customtkinter.CTkFont(family="Segoe UI", size=14, weight="bold"))
        dev_label.grid(row=0, column=0, padx=(10, 0), sticky="nw")

        dev_link = customtkinter.CTkLabel(credits_frame, text="GitHub", font=("Segoe UI", 14, "underline"), text_color="dodgerblue", cursor="pointinghand")
        dev_link.grid(row=1, column=0, padx=(10, 0), sticky="nw")
        dev_link.bind("<Button-1>", lambda e: self.open_url("https://github.com/sleepytil"))

        webhook_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Webhook URL:",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20))
        webhook_label.grid(column=0, row=0, columnspan=2, padx=(10, 0), pady=(5, 0), sticky="w")

        webhook_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                       width=500, textvariable=self.webhookURL)
        webhook_field.grid(row=0, column=1, padx=(144, 0), pady=(10, 0), sticky="w")
        if self.multi_webhook.get() == "1":
            webhook_field.configure(state="disabled", text_color="gray")
            self.webhookURL.set("Multi-Webhook On")

        ps_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Private Server URL:",
                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
        ps_label.grid(column=0, row=1, padx=(10, 0), pady=(20, 0), columnspan=2, sticky="w")

        ps_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                  width=470, textvariable=self.psURL)
        ps_field.grid(row=1, column=1, padx=(181, 0), pady=(23, 0), sticky="w")

        userid_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Discord User ID:",
                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
        userid_label.grid(column=0, row=2, padx=(10, 0), pady=(20, 0), columnspan=2, sticky="w")

        userid_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                  width=470, textvariable=self.userID)
        userid_field.grid(row=2, column=1, padx=(156, 0), pady=(23, 0), sticky="w")

        detection_toggle = customtkinter.CTkCheckBox(tabview.tab("Config"), text="Aura Detection",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                             variable=self.aura_detection, command=self.auradetection_toggle_update)
        detection_toggle.grid(row=1, column=0, columnspan=1, padx=(10, 0), pady=(10, 0), sticky="w")

        auramin_label = customtkinter.CTkLabel(tabview.tab("Config"), text="Minimum Ping Rarity:",
                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
        auramin_label.grid(column=0, row=2, padx=(10, 0), pady=(20, 0), columnspan=1, sticky="w")

        anti_afk_toggle = customtkinter.CTkCheckBox(tabview.tab("Config"), text="Anti-AFK",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                             variable=self.anti_afk, command=self.anti_afk_toggle_update)
        anti_afk_toggle.grid(row=0, column=0, columnspan=1, padx=(10, 0), pady=(10, 0), sticky="w")

        auramin_field = customtkinter.CTkEntry(tabview.tab("Config"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                  width=470, textvariable=self.auraMin)
        auramin_field.grid(row=2, column=1, padx=(8, 0), pady=(23, 0), sticky="w")

        total_biomes_label = customtkinter.CTkLabel(tabview.tab("Stats"), text="Total Biomes Found:",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20))
        total_biomes_label.grid(column=0, row=0, columnspan=2, padx=(10, 0), pady=(5, 0), sticky="w")

        self.total_biomes_amount = customtkinter.CTkLabel(tabview.tab("Stats"),
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20), text=f"{self.totalBiomesFound}")
        self.total_biomes_amount.grid(column=1, row=0, columnspan=2, padx=(195, 0), pady=(5, 0), sticky="w")
    
    def popup(self, message, title):
        applescript = """
        display dialog "{message}" ¬
        with title "{title}" ¬
        with icon caution ¬
        buttons {{"OK"}}
        """.format(message=message, title=title)

        subprocess.call("osascript -e '{}'".format(applescript), shell=True)
    
    def write_config(self):
        self.config.set('Webhook', 'webhook_url', self.webhookURL.get())
        self.config.set('Webhook', 'private_server', self.psURL.get())
        self.config.set('Webhook', 'discord_user_id', self.userID.get())
        self.config.set('Macro', 'aura_min_rarity', self.auraMin.get())
        self.config.set('Stats', 'total_biomes_discovered', str(self.totalBiomesFound))
        with open(self.config_path, 'w+') as configfile:
            self.config.write(configfile)

    def open_url(self, url):
        webbrowser.open(url, new=2, autoraise=True)
    
    def robloxRunCheck(self):
        processes = []
        for i in psutil.process_iter():
            try:
                processes.append(i.name())
            except:
                pass
        return "RobloxPlayer" in processes
    
    def loadAuraInfo(self):
        url = "https://raw.githubusercontent.com/sleepytil/Zen-Macro/refs/heads/main/assets/aura_info.json"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict):
                return data
            return {}
        except Exception as e:
            print(f"Error loading aura info: {e}")
            return {}

    def startMacro(self):
        if self.started: return
        embed = discord_webhook.DiscordEmbed(description="> ### Macro Started\n**Join our Discord server**:\nhttps://discord.gg/xymDbw7jJV",
                                             color="00FF00")
        if self.multi_webhook.get() != "1":
            embed.set_description("> ### **Macro Started**\n> **Webhooks Active**: 1\n\n**Join our Discord server**:\nhttps://discord.gg/xymDbw7jJV")
        else:
            embed.set_description(f"> ### **Macro Started**\n> **Webhooks Active**: {len(self.webhook_urls)}\n\n**Join our Discord server**:\nhttps://discord.gg/xymDbw7jJV")
        embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
        embed.set_thumbnail(url="https://sleepytil.github.io/images/macrostart.png")
        embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
        if self.multi_webhook.get() != "1":
            if "discord.com" not in self.webhookURL.get() or "https://" not in self.webhookURL.get():
                self.popup("Invalid or missing webhook link.", "Error")
                self.stop()
                return
            starting_webhook = discord_webhook.DiscordWebhook(url=self.webhookURL.get())
            starting_webhook.add_embed(embed)
            starting_webhook.execute()
        else:
            for url in self.webhook_urls:
                starting_webhook = discord_webhook.DiscordWebhook(url=url)
                starting_webhook.add_embed(embed)
                starting_webhook.execute()
        self.started = True
        # write config data
        self.write_config()
        
        if self.robloxRunCheck():
            self.roblox_open = True
            print("Roblox is open.")
            self.title("Zen (Running)")
            self.state_label.configure(text="Macro Started")
        else:
            print("Roblox is closed, waiting for Roblox to start...")
            self.title("Zen (Paused)")
            self.state_label.configure(text="Macro Paused")
            while True:
                if not self.stopped:
                    self.update()
                else:
                    if not self.destroyed:
                        self.destroy()
                    sys.exit()
                check = self.robloxRunCheck()
                if check:
                    break
                time.sleep(0.1)
        self.macro_start_time = time.time()
        time.sleep(5)
        latest_log = self.getLatestLogFile()
        if not latest_log:
            # logger.info(print("No log files found."))
            print("No log files found.")
            return
        with open(latest_log, 'r', encoding='utf-8') as self.file:
            print(f"Using log file: {latest_log}")
            print()
            # logger.info(f"Using log file: {latest_log}")
            self.title("Zen (Running)")
            self.state_label.configure(text="Macro Started")
            self.check_for_hover_text(self.file)
            for line in self.file:
               if "[FLog::UpdateController] version response:" in line:
                    found_update_version = True
                    try:
                       json_data_start = line.find('{"version')
                       if json_data_start != -1:
                           json_data = json.loads(line[json_data_start:])
                           update_version = json_data.get("clientVersionUpload", "")
                        #    logger.info("Update version found: " + update_version)
                           print("Update version found: " + update_version)
                    except:
                       print("Encountered error while parsing JSON to find Roblox update version.")
                    #    logger.error("Encountered error while parsing JSON to find Roblox update version.")
                    #    stop()
                    # if update_version == last_roblox_version and update_version != "":
                    #    pass
                    # else:
                    #    last_roblox_version = update_version
                       # write new version to config
                    #    config.set('Macro', 'last_roblox_version', last_roblox_version)
                    #    with open(config_name, 'w+') as configfile:
                        #    config.write(configfile)

    def getLatestLogFile(self):
        files = os.listdir(self.log_directory)
        paths = [os.path.join(self.log_directory, basename) for basename in files]
        return max(paths, key=os.path.getctime)
    
    def check_for_hover_text(self, file):
        last_event = None
        last_aura = None
        file.seek(0, 2)
        index = time.time()
        while True:
            if not self.stopped:
                self.update()
            else:
                if not self.destroyed:
                    self.destroy()
                sys.exit()
            check = self.robloxRunCheck()
            if check:
                check_index = time.time() - index
                if check_index > 150:
                    index = time.time()
                    if self.anti_afk.get() == 1:
                        pyautogui.press("space")
                        print("ANTI-AFK: Pressed space to prevent kick...")
                    else:
                        print("ANTI-AFK: Not-enabled, skipping function...")
                line = file.readline()
                if line:
                    print(line)
                    if '"command":"SetRichPresence"' in line:
                        try:
                            json_data_start = line.find('{"command":"SetRichPresence"')
                            if json_data_start != -1:
                                json_data = json.loads(line[json_data_start:])
                                event = json_data.get("data", {}).get("largeImage", {}).get("hoverText", "")
                                state = json_data.get("data", {}).get("state", "")
                                aura = state[10:-1]
                                if event and event != last_event:
                                    if self.multi_webhook.get() != "1":
                                        if "discord.com" not in self.webhookURL.get() or "https://" not in self.webhookURL.get():
                                            self.popup("Invalid or missing webhook link.", "Error")
                                            self.stop()
                                            return
                                        webhook = discord_webhook.DiscordWebhook(url=self.webhookURL.get())
                                        if event == "NORMAL":
                                            if last_event is not None:
                                                event_biome_colour = ""
                                                if last_event in self.biome_colours:
                                                    event_biome_colour = self.biome_colours[last_event]
                                                else:
                                                    event_biome_colour = "FFFFFF"
                                                print(time.strftime('%H:%M:%S') + f": Biome Ended - " + last_event)
                                                embed = discord_webhook.DiscordEmbed(description=f"> ### Biome Ended - {last_event}",
                                                                                color=event_biome_colour)
                                                embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                                                embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                                                webhook.add_embed(embed)
                                                webhook.execute()
                                            else:
                                                pass
                                        else:
                                            print(time.strftime('%H:%M:%S') + f": Biome Started - {event}")
                                            self.totalBiomesFound = int(self.totalBiomesFound) + 1
                                            self.total_biomes_amount.configure(text=f"{self.totalBiomesFound}")
                                            event_biome_colour = ""
                                            biomeEndingTime = ""
                                            if event in self.biome_colours:
                                                event_biome_colour = self.biome_colours[event]
                                            else:
                                                event_biome_colour = "FFFFFF"
                                            biomeEndTimeFormatted = ""
                                            embed = discord_webhook.DiscordEmbed(color=event_biome_colour)
                                            if event in self.biome_times and event != "EGGLAND":
                                                biomeEndingTime = int(time.time()) + int(self.biome_times[event])
                                                biomeEndTimeFormatted = f"<t:{biomeEndingTime}:R>"
                                                event_biome_colour = self.biome_colours[event]
                                                embed.set_description(f"> ### Biome Started - {event}\n[Join Private Server]({self.psURL.get()})\n-# Ends {biomeEndTimeFormatted}")
                                            else:
                                                embed.set_description(f"> ### Biome Started - {event}\n[Join Private Server]({self.psURL.get()})")
                                            
                                            embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                                            embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/" + event.replace(" ", "%20") + ".png")
                                            webhook.add_embed(embed)
                                            if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                webhook.set_content("@everyone")
                                            webhook.execute()
                                            if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                self.send_rare_biome_screenshot(event)
                                    else:
                                        if event == "NORMAL":
                                            if last_event is not None:
                                                print(time.strftime('%H:%M:%S') + f": Biome Ended - " + last_event)
                                                event_biome_colour = ""
                                                if last_event in self.biome_colours:
                                                    event_biome_colour = self.biome_colours[last_event]
                                                else:
                                                    event_biome_colour = "FFFFFF"
                                                
                                                for url in self.webhook_urls:
                                                    webhook = discord_webhook.DiscordWebhook(url=url)
                                                    embed = discord_webhook.DiscordEmbed(description=f"> ### Biome Ended - {last_event}",
                                                                                color=event_biome_colour)
                                                    embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                                                    embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                                                    webhook.add_embed(embed)
                                                    webhook.execute()
                                            else:
                                                pass
                                        else:
                                            print(time.strftime('%H:%M:%S') + f": Biome Started - {event}")
                                            self.totalBiomesFound = int(self.totalBiomesFound) + 1
                                            self.total_biomes_amount.configure(text=f"{self.totalBiomesFound}")
                                            event_biome_colour = ""
                                            biomeEndingTime = ""
                                            if event in self.biome_colours:
                                                event_biome_colour = self.biome_colours[event]
                                            else:
                                                event_biome_colour = "FFFFFF"
                                            biomeEndTimeFormatted = ""
                                            
                                            
                                            for url in self.webhook_urls:
                                                embed = discord_webhook.DiscordEmbed(color=event_biome_colour)
                                                if event in self.biome_times and event != "EGGLAND":
                                                    biomeEndingTime = int(time.time()) + int(self.biome_times[event])
                                                    biomeEndTimeFormatted = f"<t:{biomeEndingTime}:R>"
                                                    event_biome_colour = self.biome_colours[event]
                                                    embed.set_description(f"> ### Biome Started - {event}\n[Join Private Server]({self.psURL.get()})\n-# Ends {biomeEndTimeFormatted}")
                                                else:
                                                    embed.set_description(f"> ### Biome Started - {event}\n[Join Private Server]({self.psURL.get()})")
                                                embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                                                embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                                                embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/" + event.replace(" ", "%20") + ".png")
                                                webhook = discord_webhook.DiscordWebhook(url=url)
                                                webhook.add_embed(embed)
                                                if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                    webhook.set_content("@everyone")
                                                webhook.execute()
                                            if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                self.send_rare_biome_screenshot(event)
                                    last_event = event
                                if state and aura != last_aura and aura != "n":
                                    if self.aura_detection.get() == 1 and aura != "None":
                                        self.send_aura_screenshot(aura)
                                    last_aura = aura
                        except json.JSONDecodeError:
                            print("Error decoding JSON")
                else:
                    time.sleep(0.1)
            else:
                print("Roblox is closed, waiting for Roblox to start...")
                if self.multi_webhook.get() != "1":
                    if "discord.com" not in self.webhookURL.get() or "https://" not in self.webhookURL.get():
                        self.popup("Invalid or missing webhook link.", "Error")
                        self.stop()
                        return
                    close_webhook = discord_webhook.DiscordWebhook(url=url)
                    close_embed = discord_webhook.DiscordEmbed(description=f"> ### Roblox Closed/Crashed",
                                                               color="FF0000")
                    close_embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                    close_embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                    close_webhook.add_embed(close_embed)
                    close_webhook.execute()
                else:
                    for url in self.webhook_urls:
                        close_webhook = discord_webhook.DiscordWebhook(url=url)
                        close_embed = discord_webhook.DiscordEmbed(description=f"> ### Roblox Closed/Crashed",
                                                                   color="FF0000")
                        close_embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                        close_embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                        close_webhook.add_embed(close_embed)
                        close_webhook.execute()

                self.title("Zen (Paused)")
                while True:
                    if not self.stopped:
                        self.update()
                    else:
                        if not self.destroyed:
                            self.destroy()
                        sys.exit()
                    check = self.is_roblox_running()
                    if check:
                        break
                    time.sleep(0.1)
                time.sleep(5)
                latest_log = self.get_latest_log_file()
                if not latest_log:
                    self.logger.info("No log files found.")
                    print("No log files found.")
                    return
                with open(latest_log, 'r', encoding='utf-8') as file:
                    print(f"Using log file: {latest_log}")
                    print()
                    self.logger.info(f"Using log file: {latest_log}")
                    self.title("Zen (Running)")
                    self.check_for_hover_text(file)

    def auradetection_toggle_update(self):
        if self.aura_detection.get() == 1:
            self.popup("You are about to be prompted to enable screen recording permissions for this application.\nThis is required for aura detection to work, "
                  "as the macro will screenshot the game to show what aura was equipped.\n\nAfter enabling permissions, you will need to restart the macro.",
                  "Aura Detection")
            os.makedirs("images", exist_ok=True)
            filename = os.path.join("images", f"screenshot_{int(time.time())}.png")
            img = pyautogui.screenshot()
            img.save(filename)
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Failed to delete screenshot {filename}: {e}")
        self.config.set('Macro', 'aura_detection', str(self.aura_detection.get()))
        with open(self.config_path, 'w+') as configfile:
            self.config.write(configfile)
    
    def anti_afk_toggle_update(self):
        if self.anti_afk.get() == 1:
            self.popup("You are about to be prompted to enable accessibility permissions for this application.\nThis is required for the anti-AFK feature to work, "
                  "as the macro will initiate keystrokes to ensure you don't disconnect.\n\nAfter enabling permissions, you will need to restart the macro.",
                  "Aura Detection")
            pyautogui.press("space")
        self.config.set('Macro', 'anti_afk', str(self.anti_afk.get()))
        with open(self.config_path, 'w+') as configfile:
            self.config.write(configfile)

    def stop(self):
        # write config data
        self.write_config()

        # end webhook
        if self.started and not self.stopped:
            if self.multi_webhook.get() != "1":
                if "discord.com" in self.webhookURL.get() and "https://" in self.webhookURL.get():
                    ending_webhook = discord_webhook.DiscordWebhook(url=self.webhookURL.get())
                    ending_embed = discord_webhook.DiscordEmbed(description=f"> ### Macro Stopped\n**Runtime**: `{str(datetime.timedelta(seconds=int((time.time() - self.macro_start_time))))}`\n**Join our Discord server**:\nhttps://discord.gg/xymDbw7jJV",
                                                                color="FF0000")
                    ending_embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                    ending_embed.set_thumbnail(url="https://sleepytil.github.io/images/macrostop.png")
                    ending_embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                    ending_webhook.add_embed(ending_embed)
                    ending_webhook.execute()

            else:
                ending_embed = discord_webhook.DiscordEmbed(description=f"> ### Macro Stopped\n**Runtime**: `{str(datetime.timedelta(seconds=int((time.time() - self.macro_start_time))))}`\n**Join our Discord server**:\nhttps://discord.gg/xymDbw7jJV",
                                                            color="FF0000")
                ending_embed.set_footer("Zen (2.2)", icon_url="https://sleepytil.github.io/images/zenicon.png")
                ending_embed.set_thumbnail(url="https://sleepytil.github.io/images/macrostop.png")
                ending_embed.set_timestamp(datetime.datetime.now(datetime.timezone.utc))
                for url in self.webhook_urls:
                    ending_webhook = discord_webhook.DiscordWebhook(url=url)
                    ending_webhook.add_embed(ending_embed)
                    ending_webhook.execute()
        else:
            sys.exit()
        self.stopped = True
    
    def send_rare_biome_screenshot(self, biome):
        os.makedirs("images", exist_ok=True)
        filename = os.path.join("images", f"screenshot_{int(time.time())}.png")
        img = pyautogui.screenshot()
        img.save(filename)
        try:
            content = ""
            icon_url = "https://sleepytil.github.io/images/zenicon.png"
            current_utc_time = str(datetime.datetime.now(datetime.timezone.utc))
            embed = {
                "description": f"> ### Biome Screenshot - {biome}",
                "color": 0xffffff,
                "footer": {"text": "Zen (2.2)", "icon_url": icon_url},
                "timestamp": current_utc_time
            }
            if self.multi_webhook.get() != "1":
                if "discord.com" in self.webhookURL.get() and "https://" in self.webhookURL.get():
                    try:
                        embed_copy = dict(embed)
                        embed_copy["image"] = {"url": f"attachment://{os.path.basename(filename)}"}
                        with open(filename, "rb") as image_file:
                            files = {"file": (os.path.basename(filename), image_file, "image/png")}
                            data = {"payload_json": json.dumps({"content": content, "embeds": [embed_copy]})}
                            requests.post(self.webhookURL.get(), data=data, files=files, timeout=10)
                    except Exception as e:
                        try:
                            print(f"Failed to send inventory screenshot to {self.webhookURL.get()}: {e}")
                        except Exception:
                            pass
            else:
                for url in self.webhook_urls:
                    try:
                        embed_copy = dict(embed)
                        embed_copy["image"] = {"url": f"attachment://{os.path.basename(filename)}"}
                        with open(filename, "rb") as image_file:
                            files = {"file": (os.path.basename(filename), image_file, "image/png")}
                            data = {"payload_json": json.dumps({"content": content, "embeds": [embed_copy]})}
                            requests.post(url, data=data, files=files, timeout=10)
                    except Exception as e:
                        try:
                            print(f"Failed to send inventory screenshot to {url}: {e}")
                        except Exception:
                            pass
        except Exception as e: 
            print(e, "- Error taking/sending ingame screenshot")
        finally:
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Failed to delete screenshot {filename}: {e}")
    
    def load_notice_tab(self):
        url = "https://raw.githubusercontent.com/sleepytil/Zen-Macro/refs/heads/main/assets/notice_tab.txt"
        data = ""
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.text
        except Exception as e:
            print(f"Error loading notice_tab.txt from {url}: {e}")
            self.error_logging(e, f"Error loading notice_tab.txt from {url}")

        return data
    
    def send_aura_screenshot(self, aura):
        os.makedirs("images", exist_ok=True)
        filename = os.path.join("images", f"screenshot_{int(time.time())}.png")
        img = pyautogui.screenshot()
        img.save(filename)
        try:
            icon_url = "https://sleepytil.github.io/images/zenicon.png"
            current_utc_time = str(datetime.datetime.now(datetime.timezone.utc))
            embed = {}
            fAura = aura.replace("_", " : ")
            content = ""
            if aura in self.auraRarities:
                rarity = self.auraRarities[aura]["rarity"]
                fRarity = f"{rarity:,}"
                try:
                    if self.auraRarities[aura]["craftable"] == True:
                        fRarity += " [**CRAFTED**]"
                    else:
                        pass
                except Exception:
                    pass
                embedColour = 0xffffff

                if rarity >= int(self.auraMin.get()):
                    content = f"<@{self.userID.get()}>"
                
                if rarity >= 999999999:
                    embedColour = 0x7fffd4
                elif rarity >= 99999999:
                    embedColour = 0xff2c2c
                elif rarity >= 9999999:
                    embedColour = 0x00008b
                elif rarity >= 999999:
                    embedColour = 0xff69b4
                else:
                    embedColour = 0xffffff



                embed = {
                    "description": f"> ### Aura Equipped - {fAura}\n> **Rarity**: 1 in {fRarity}",
                    "color": embedColour,
                    "footer": {"text": "Zen (2.2)", "icon_url": icon_url},
                    "timestamp": current_utc_time
                }
                if self.multi_webhook.get() != "1":
                    if "discord.com" in self.webhookURL.get() and "https://" in self.webhookURL.get():
                        try:
                            embed_copy = dict(embed)
                            embed_copy["image"] = {"url": f"attachment://{os.path.basename(filename)}"}
                            with open(filename, "rb") as image_file:
                                files = {"file": (os.path.basename(filename), image_file, "image/png")}
                                data = {"payload_json": json.dumps({"content": content, "embeds": [embed_copy]})}
                                requests.post(self.webhookURL.get(), data=data, files=files, timeout=10)
                        except Exception as e:
                            try:
                                print(f"Failed to send aura screenshot to {self.webhookURL.get()}: {e}")
                            except Exception:
                                pass
                else:
                    for url in self.webhook_urls:
                        try:
                            embed_copy = dict(embed)
                            embed_copy["image"] = {"url": f"attachment://{os.path.basename(filename)}"}
                            with open(filename, "rb") as image_file:
                                files = {"file": (os.path.basename(filename), image_file, "image/png")}
                                data = {"payload_json": json.dumps({"content": content, "embeds": [embed_copy]})}
                                requests.post(url, data=data, files=files, timeout=10)
                        except Exception as e:
                            try:
                                print(f"Failed to send aura screenshot to {url}: {e}")
                            except Exception:
                                pass
            else:
                embed = {
                    "description": f"> ### Aura Equipped - {fAura}",
                    "color": 0xffffff,
                    "footer": {"text": "Zen (2.2)", "icon_url": icon_url},
                    "timestamp": current_utc_time
                }
                if self.multi_webhook.get() != "1":
                    if "discord.com" in self.webhookURL.get() and "https://" in self.webhookURL.get():
                        try:
                            embed_copy = dict(embed)
                            embed_copy["image"] = {"url": f"attachment://{os.path.basename(filename)}"}
                            with open(filename, "rb") as image_file:
                                files = {"file": (os.path.basename(filename), image_file, "image/png")}
                                data = {"payload_json": json.dumps({"content": content, "embeds": [embed_copy]})}
                                requests.post(self.webhookURL.get(), data=data, files=files, timeout=10)
                        except Exception as e:
                            try:
                                print(f"Failed to send aura screenshot to {self.webhookURL.get()}: {e}")
                            except Exception:
                                pass
                else:
                    for url in self.webhook_urls:
                        try:
                            embed_copy = dict(embed)
                            embed_copy["image"] = {"url": f"attachment://{os.path.basename(filename)}"}
                            with open(filename, "rb") as image_file:
                                files = {"file": (os.path.basename(filename), image_file, "image/png")}
                                data = {"payload_json": json.dumps({"content": content, "embeds": [embed_copy]})}
                                requests.post(url, data=data, files=files, timeout=10)
                        except Exception as e:
                            try:
                                print(f"Failed to send aura screenshot to {url}: {e}")
                            except Exception:
                                pass
        except Exception as e: 
            print(e, "- Error taking/sending ingame screenshot")
        finally:
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Failed to delete screenshot {filename}: {e}")


root = macroActivity()
root.mainloop()