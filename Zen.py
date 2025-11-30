import os
import time
import json
import webbrowser
import psutil
import discord_webhook
import configparser
import customtkinter
import logging
import sys
from PIL import Image
import subprocess
import platformdirs
import datetime
print("""
      Zen Macro (by sleepytil)
      
      [DEBUG INFO]
      Version: v1.3.2 (30 November 2025)
      Support: https://discord.gg/solsniper
      """)
logging.basicConfig(
    filename='crash.log',  # Optional: Specify a file to log to
    level=logging.INFO,  # Set the minimum level for logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Customize the log format
)

logger = logging.getLogger('mylogger')

def popup(message, title):
    applescript = """
    display dialog "{message}" ¬
    with title "{title}" ¬
    with icon caution ¬
    buttons {{"OK"}}
    """.format(message=message, title=title)

    subprocess.call("osascript -e '{}'".format(applescript), shell=True)

CMD = '''
on run argv
  display notification (item 2 of argv) with title (item 1 of argv)
end run
'''

def notify(title, text):
  subprocess.call(['osascript', '-e', CMD, title, text])

# Example uses:
def my_handler(types, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))
    popup("Check crash.log for information on this crash.", "Crashed!")
    sys.exit()

# exception handler / logger
sys.excepthook = my_handler

# create UI window
customtkinter.set_default_color_theme("dark-blue")
root = customtkinter.CTk()
root.title("Zen")
root.geometry('505x285')
root.resizable(False, False)
dirname = os.path.dirname(__file__)
tabview = customtkinter.CTkTabview(root, width=505, height=230)
tabview.grid(row=0, column=0, sticky='nsew', columnspan=75)
tabview.add("Webhook")
tabview.add("Macro")
tabview.add("Credits")
tabview._segmented_button.configure(font=customtkinter.CTkFont(family="Segoe UI", size=16))
tabview._segmented_button.grid(sticky="w", padx=15)

# read configuration file
config_name = 'config.ini'
config = configparser.ConfigParser()
if not os.path.exists(config_name):
    logger.info("Config file not found, creating one...")
    print("Config file not found, creating one...")
    config['Webhook'] = {'webhook_url': "", 'private_server': "", "discord_user_id": "",  'multi_webhook': "0", 'multi_webhook_urls': ""}
    config['Macro'] = {'aura_detection': "0", 'username_override': "", 'last_roblox_version': "", 'aura_notif': "0", 'aura_ping': "0"}
    with open(config_name, 'w') as configfile:
        config.write(configfile)
config.read(config_name)
webhookURL = customtkinter.StringVar(root, config['Webhook']['webhook_url'])
psURL = customtkinter.StringVar(root, config['Webhook']['private_server'])
discID = customtkinter.StringVar(root, config['Webhook']['discord_user_id'])
multi_webhook = customtkinter.StringVar(root, config['Webhook']['multi_webhook'])
if multi_webhook.get() != "1" and webhookURL.get() == "Multi-Webhook On":
    webhookURL.set("")
webhook_urls_string = customtkinter.StringVar(root, config['Webhook']['multi_webhook_urls'])
webhook_urls = webhook_urls_string.get().split()

# variables
last_roblox_version = config['Macro']['last_roblox_version']
username_override = config['Macro']['username_override']
roblox_open = False
log_directory = platformdirs.user_log_dir("Roblox", None)
biome_colors = {"NORMAL": "ffffff", "SAND STORM": "F4C27C", "HELL": "5C1219", "STARFALL": "6784E0", "CORRUPTION": "9042FF", "NULL": "000000", "GLITCHED": "65FF65", "WINDY": "91F7FF", "SNOWY": "C4F5F6", "RAINY": "4385FF", "DREAMSPACE": "ff7dff", "BLAZING SUN": "ffee8c", "PUMPKIN MOON": "FFA500", "GRAVEYARD": "646464", "BLOOD RAIN": "FF0000", "CYBERSPACE": "03045E"}
biome_times = {"SAND STORM": 600, "HELL": 660, "STARFALL": 600, "CORRUPTION": 660, "NULL": 99, "GLITCHED": 164, "WINDY": 120, "SNOWY": 120, "RAINY": 120, "DREAMSPACE": 128, "BLAZING SUN": 180, "PUMPKIN MOON": 300, "GRAVEYARD": 300, "BLOOD RAIN": 600, "CYBERSPACE": 720}
started = False
stopped = False
paused = False
destroyed = False
debug_window = False
tlw_open = False
aura_detection = customtkinter.IntVar(root, int(config['Macro']['aura_detection']))
aura_notif = customtkinter.IntVar(root, int(config['Macro']['aura_notif']))
aura_ping = customtkinter.IntVar(root, int(config['Macro']['aura_ping']))
roblox_username = config['Macro']['username_override']


def stop():
    global stopped
    # write config data
    config.set('Webhook', 'webhook_url', webhookURL.get())
    config.set('Webhook', 'private_server', psURL.get())
    with open(config_name, 'w+') as configfile:
        config.write(configfile)

    # end webhook
    if started and not stopped:
        if multi_webhook.get() != "1":
            if "discord.com" in webhookURL.get() and "https://" in webhookURL.get():
                ending_webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                ending_embed = discord_webhook.DiscordEmbed(
                    title="`Macro Stopped`",
                    timestamp=datetime.datetime.now(datetime.timezone.utc))
                ending_embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                ending_webhook.add_embed(ending_embed)
                ending_webhook.execute()

        else:
            ending_embed = discord_webhook.DiscordEmbed(
                title="`Macro Stopped`",
                timestamp=datetime.datetime.now(datetime.timezone.utc))
            ending_embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
            for url in webhook_urls:
                ending_webhook = discord_webhook.DiscordWebhook(url=url)
                ending_webhook.add_embed(ending_embed)
                ending_webhook.execute()
    else:
        sys.exit()
    stopped = True

if multi_webhook == "1":
    if len(webhook_urls) < 2:
        popup("there's no reason to use multi-webhook... without multiple webhooks??", "bruh are you serious")
    elif len(webhook_urls) > 14:
        if len(webhook_urls) > 49:
            popup("you've gotta be doing this on purpose now... you don't need this many webhooks", "this is ridiculous")
        else:
            popup("bro you do not need this many webhooks", "okay dude wtf")
    stop()


def x_stop():
    global destroyed
    destroyed = True
    stop()


def get_latest_log_file():
    files = os.listdir(log_directory)
    paths = [os.path.join(log_directory, basename) for basename in files]
    return max(paths, key=os.path.getctime)


def is_roblox_running():
    processes = []
    for i in psutil.process_iter():
        try:
            processes.append(i.name())
        except:
            pass
    return "RobloxPlayer" in processes

def auranotif_toggle_update():
    config.set('Macro', 'aura_notif', str(aura_notif.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def auraping_toggle_update():
    config.set('Macro', 'aura_ping', str(aura_ping.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)

def jester_toggle_update():
    config.set('Macro', 'jester', str(aura_ping.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def check_for_hover_text(file):
    last_event = None
    last_aura = None
    file.seek(0, 2)
    while True:
        if not stopped:
            root.update()
        else:
            if not destroyed:
                root.destroy()
            sys.exit()
        check = is_roblox_running()
        if check:
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
                                if multi_webhook.get() != "1":
                                    if "discord.com" not in webhookURL.get() or "https://" not in webhookURL.get():
                                        popup("Invalid or missing webhook link.", "Error")
                                        stop()
                                        return
                                    webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                    if event == "NORMAL":
                                        if last_event is not None:
                                            print(time.strftime('%H:%M:%S') + f": Biome Ended - " + last_event)
                                            embed = discord_webhook.DiscordEmbed(
                                                timestamp=datetime.datetime.now(datetime.timezone.utc),
                                                color=biome_colors[last_event],
                                                title=f"`Biome Ended: {last_event}`")
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/" + last_event.replace(" ", "%20") + ".png")
                                            embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                            webhook.add_embed(embed)
                                            webhook.execute()
                                        else:
                                            pass
                                    else:
                                        print(time.strftime('%H:%M:%S') + f": Biome Started - {event}")
                                        biomeEndingTime = int(time.time()) + biome_times[event]
                                        embed = discord_webhook.DiscordEmbed(title=f"`Biome Started: {event}`",timestamp=datetime.datetime.now(datetime.timezone.utc), color=biome_colors[event])
                                        embed.description = "\n[Join Server](" + psURL.get() + ")\n-# Ends <t:" + str(biomeEndingTime) + ":R>"
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/" + event.replace(" ", "%20") + ".png")
                                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                        webhook.add_embed(embed)
                                        if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                            webhook.set_content("@everyone")
                                            notify("Zen", "Biome Started: " + event)
                                        webhook.execute()
                                else:
                                    if event == "NORMAL":
                                        if last_event is not None:
                                            print(time.strftime('%H:%M:%S') + f": Biome Ended - " + last_event)
                                            for url in webhook_urls:
                                                webhook = discord_webhook.DiscordWebhook(url=url)
                                                embed = discord_webhook.DiscordEmbed(
                                                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                                                    color=biome_colors[last_event],
                                                    title=f"`Biome Ended: {last_event}`")
                                                embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/" + last_event.replace(" ", "%20") + ".png")
                                                embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                                webhook.add_embed(embed)
                                                webhook.execute()
                                        else:
                                            pass
                                    else:
                                        print(time.strftime('%H:%M:%S') + f": Biome Started - {event}")
                                        biomeEndingTime = int(time.time()) + biome_times[event]            
                                        for url in webhook_urls:
                                            embed = discord_webhook.DiscordEmbed(title=f"`Biome Started: {event}`",timestamp=datetime.datetime.now(datetime.timezone.utc), color=biome_colors[event])
                                            embed.description = "\n[Join Server](" + psURL.get() + ")\n-# Ends <t:" + str(biomeEndingTime) + ":R>"
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/" + event.replace(" ", "%20") + ".png")
                                            embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                            webhook = discord_webhook.DiscordWebhook(url=url)
                                            webhook.add_embed(embed)
                                            if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                webhook.set_content("@everyone")
                                            webhook.execute()
                                        if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                            notify("Zen", "Biome Started: " + event)
                                last_event = event
                            if state and aura != last_aura and aura != "n":
                                if aura_detection.get() == 1 and aura != "None":
                                    if multi_webhook.get() != "1":
                                        if "discord.com" not in webhookURL.get() or "https://" not in webhookURL.get():
                                            popup("Invalid or missing webhook link.", "Error")
                                            stop()
                                            return
                                        webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                        print(time.strftime('%H:%M:%S') + f": Aura Equipped - {aura}")
                                        embed = discord_webhook.DiscordEmbed(
                                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                                            title=f"`Aura Equipped: {aura}`")
                                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                        webhook.add_embed(embed)
                                        webhook.execute()
                                    else:
                                        print(time.strftime('%H:%M:%S') + f": Aura Equipped - {aura}")
                                        for url in webhook_urls:
                                            webhook = discord_webhook.DiscordWebhook(url=url)
                                            embed = discord_webhook.DiscordEmbed(
                                                timestamp=datetime.datetime.now(datetime.timezone.utc),
                                                title=f"`Aura Equipped: {aura}`")
                                            embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                            webhook.add_embed(embed)
                                            webhook.execute()
                                last_aura = aura
                    except json.JSONDecodeError:
                        print("Error decoding JSON")
                elif "Incoming MessageReceived Status:" in line:
                    # check if message is specially formatted (aura roll, jester)
                    if "</font>" in line:
                        if aura_detection.get() == 1 and "HAS FOUND" in line:
                            # handle HAS FOUND message
                            userdata, _, auradata = line.partition("HAS FOUND")
                            auradata = auradata[1:-8]
                            aura, _, rarity = auradata.partition(", ")
                            rarity = rarity[15:-1]
                            int_rarity = rarity.replace(',', '')
                            message_color = line[line.find('<font color="#') + len('<font color="#'):line.find('">', line.find('<font color="#'))]
                            # remove [From Biome]
                            int_rarity = int_rarity.split()[0]
                            if int(int_rarity) < 99999 and aura != "Fault" and "\u00e2\u02dc\u2026" not in aura:
                               continue
                            _, _, full_user = userdata.rpartition(">")
                            full_user = full_user[:-1]
                            if "(" in full_user:
                                _, _, rolled_username = full_user.partition("(")
                                rolled_username = rolled_username[1:-1]
                            else:
                                rolled_username = full_user[1:]
                            if rolled_username == roblox_username.strip():
                                if multi_webhook.get() != "1":
                                    webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - {aura}")
                                    embed = discord_webhook.DiscordEmbed(
                                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                                        title=f"`You rolled {aura}!`",
                                        description="**1 in " + rarity + "**",
                                        color=message_color)
                                    embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                    if message_color == "ff73fd":
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/MYTHIC.png")
                                    elif message_color == "200cff":
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/EXALTED.png")
                                    elif message_color == "ff3892":
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/GLORIOUS.png")
                                    else:
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/ANY.png")
                                    # embed.set_thumbnail(url=aura_images[aura.lower()])
                                    webhook.add_embed(embed)
                                    if aura_ping.get() == 1:
                                        webhook.set_content(f"<@{discID.get()}>")
                                    webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled " + aura + "!")
                                else:
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - {aura}")
                                    for url in webhook_urls:
                                        webhook = discord_webhook.DiscordWebhook(url=url)
                                        embed = discord_webhook.DiscordEmbed(
                                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                                            title=f"`You rolled {aura}!`",
                                            description="**1 in " + rarity + "**",
                                            color=message_color)
                                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                        if message_color == "ff73fd":
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/MYTHIC.png")
                                        elif message_color == "200cff":
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/EXALTED.png")
                                        elif message_color == "ff3892":
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/GLORIOUS.png")
                                        else:
                                            embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/ANY.png")
                                        # embed.set_thumbnail(url=aura_images[aura.lower()])
                                        webhook.add_embed(embed)
                                        if aura_ping.get() == 1:
                                            webhook.set_content(f"<@{discID.get()}>")
                                        webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled " + aura + "!")
                        elif aura_detection.get() == 1 and "The Blinding Light has devoured" in line:
                            if roblox_username in line:
                                if multi_webhook.get() != "1":
                                    webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - Luminosity")
                                    embed = discord_webhook.DiscordEmbed(
                                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                                        title=f"`The Blinding Light has devoured {roblox_username}`",
                                        description="**1 in 1,200,000,000**",
                                        color="98b7e0")
                                    embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                    embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/Luminosity.png")
                                    webhook.add_embed(embed)
                                    if aura_ping.get() == 1:
                                        webhook.set_content(f"<@{discID.get()}>")
                                    webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled Luminosity!")
                                else:
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - Luminosity")
                                    for url in webhook_urls:
                                        webhook = discord_webhook.DiscordWebhook(url=url)
                                        embed = discord_webhook.DiscordEmbed(
                                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                                            title=f"`The Blinding Light has devoured {roblox_username}`",
                                            description="**1 in 1,200,000,000**",
                                            color="98b7e0")
                                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/Luminosity.png")
                                        webhook.add_embed(embed)
                                        if aura_ping.get() == 1:
                                            webhook.set_content(f"<@{discID.get()}>")
                                        webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled Luminosity!")
                        elif aura_detection.get() == 1 and "has become" in line:
                            if roblox_username in line:
                                if multi_webhook.get() != "1":
                                    webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - Pixelation")
                                    embed = discord_webhook.DiscordEmbed(
                                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                                        title=f"`@{roblox_username} has become PIXELATED!`",
                                        description="**1 in 1,073,741,824**",
                                        color="ff0000")
                                    embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                    embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/Pixelation.png")
                                    webhook.add_embed(embed)
                                    if aura_ping.get() == 1:
                                        webhook.set_content(f"<@{discID.get()}>")
                                    webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled Pixelation!")
                                else:
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - Pixelation")
                                    for url in webhook_urls:
                                        webhook = discord_webhook.DiscordWebhook(url=url)
                                        embed = discord_webhook.DiscordEmbed(
                                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                                            title=f"`@{roblox_username} has become PIXELATED!`",
                                            description="**1 in 1,073,741,824**",
                                            color="ff0000")
                                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/Pixelation.png")
                                        webhook.add_embed(embed)
                                        if aura_ping.get() == 1:
                                            webhook.set_content(f"<@{discID.get()}>")
                                        webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled Pixelation!")
                        elif aura_detection.get() == 1 and "???????" in line:
                            if roblox_username in line:
                                if multi_webhook.get() != "1":
                                    webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - EQUINOX")
                                    embed = discord_webhook.DiscordEmbed(
                                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                                        title=f"`@{roblox_username} has found the [???????] between POSITIVE and NEGATIVE.`",
                                        description="**1 in 2,500,000,000**",
                                        color="000000")
                                    embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                    embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/EQUINOX.png")
                                    webhook.add_embed(embed)
                                    if aura_ping.get() == 1:
                                        webhook.set_content(f"<@{discID.get()}>")
                                    webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled EQUINOX!")
                                else:
                                    print(time.strftime('%H:%M:%S') + f": Aura Rolled - EQUINOX")
                                    for url in webhook_urls:
                                        webhook = discord_webhook.DiscordWebhook(url=url)
                                        embed = discord_webhook.DiscordEmbed(
                                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                                            title=f"`@{roblox_username} has found the [???????] between POSITIVE and NEGATIVE.`",
                                            description="**1 in 2,500,000,000**",
                                            color="000000")
                                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                        embed.set_thumbnail(url="https://sleepytil.github.io/biome_thumb/EQUINOX.png")
                                        webhook.add_embed(embed)
                                        if aura_ping.get() == 1:
                                            webhook.set_content(f"<@{discID.get()}>")
                                        webhook.execute()
                                    if aura_notif.get() == 1:
                                        notify("Zen", "You rolled EQUINOX!")
                        elif "[Merchant]: Jester has arrived on the island!!" in line:
                            if multi_webhook.get() != "1":
                                webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                print(time.strftime('%H:%M:%S') + f": Jester Spawned!")
                                embed = discord_webhook.DiscordEmbed(
                                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                                    title=f"`Jester Spawned!`",
                                    description=f"[Join Server]({psURL.get()})\n-# <t:{int(time.time())}:R>",
                                    color="a352ff"
                                )
                                embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                embed.set_thumbnail(
                                    url="https://sleepytil.github.io/biome_thumb/JESTER.png")
                                webhook.add_embed(embed)
                                webhook.set_content(f"<@{discID.get()}>")
                                webhook.execute()
                            else:
                                print(time.strftime('%H:%M:%S') + f": Jester Spawned!")
                                for url in webhook_urls:
                                    webhook = discord_webhook.DiscordWebhook(url=url)
                                    embed = discord_webhook.DiscordEmbed(
                                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                                        title=f"`Jester Spawned!`",
                                        description=f"[Join Server]({psURL.get()})\n-# <t:{int(time.time())}:R>",
                                        color="a352ff"
                                    )
                                    embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                    embed.set_thumbnail(
                                        url="https://sleepytil.github.io/biome_thumb/JESTER.png")
                                    webhook.add_embed(embed)
                                    webhook.set_content(f"<@{discID.get()}>")
                                    webhook.execute()
                    elif "[Merchant]: Mari has arrived on the island..." in line:
                        if multi_webhook.get() != "1":
                            webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                            print(time.strftime('%H:%M:%S') + f": Mari Spawned!")
                            embed = discord_webhook.DiscordEmbed(
                                timestamp=datetime.datetime.now(datetime.timezone.utc),
                                title=f"`Mari Spawned!`",
                                description=f"[Join Server]({psURL.get()})\n-# <t:{int(time.time())}:R>",
                                color="c49345"
                            )
                            embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                            embed.set_thumbnail(
                                url="https://sleepytil.github.io/biome_thumb/MARI.png")
                            webhook.add_embed(embed)
                            webhook.set_content(f"<@{discID.get()}>")
                            webhook.execute()
                        else:
                            print(time.strftime('%H:%M:%S') + f": Mari Spawned!")
                            for url in webhook_urls:
                                webhook = discord_webhook.DiscordWebhook(url=url)
                                embed = discord_webhook.DiscordEmbed(
                                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                                    title=f"`Mari Spawned!`",
                                    description=f"[Join Server]({psURL.get()})\n-# <t:{int(time.time())}:R>",
                                    color="c49345"
                                )
                                embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                                embed.set_thumbnail(
                                    url="https://sleepytil.github.io/biome_thumb/MARI.png")
                                webhook.add_embed(embed)
                                webhook.set_content(f"<@{discID.get()}>")
                                webhook.execute()
                elif 'Eden has appeared' in line and "<" in line:
                    if multi_webhook.get() != "1":
                        webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                        print(time.strftime('%H:%M:%S') + ": Eden has appeared somewhere in The Limbo.")
                        embed = discord_webhook.DiscordEmbed(
                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                            title=f"`Eden has appeared somewhere in The Limbo.`",
                            description=f"[Join Server]({psURL.get()})\n-# <t:{int(time.time())}:R>",
                            color="000000"
                        )
                        embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                        embed.set_thumbnail(
                            url="https://maxstellar.github.io/biome_thumb/eden.png")
                        webhook.add_embed(embed)
                        webhook.set_content(f"<@{discID.get()}>")
                        webhook.execute()
                    else:
                        print(time.strftime('%H:%M:%S') + ": Eden has appeared somewhere in The Limbo.")
                        for url in webhook_urls:
                            webhook = discord_webhook.DiscordWebhook(url=url)
                            embed = discord_webhook.DiscordEmbed(
                                timestamp=datetime.datetime.now(datetime.timezone.utc),
                                title=f"`Eden has appeared somewhere in The Limbo.`",
                                description=f"[Join Server]({psURL.get()})\n-# <t:{int(time.time())}:R>",
                                color="000000"
                            )
                            embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                            embed.set_thumbnail(
                                url="https://maxstellar.github.io/biome_thumb/eden.png")
                            webhook.add_embed(embed)
                            webhook.set_content(f"<@{discID.get()}>")
                            webhook.execute()
            else:
                time.sleep(0.1)
        else:
            print("Roblox is closed, waiting for Roblox to start...")
            if multi_webhook.get() != "1":
                if "discord.com" not in webhookURL.get() or "https://" not in webhookURL.get():
                    popup("Invalid or missing webhook link.", "Error")
                    stop()
                    return
                close_webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                close_embed = discord_webhook.DiscordEmbed(
                    title="`Roblox Closed/Crashed`",
                    timestamp=datetime.datetime.now(datetime.timezone.utc))
                close_embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                close_webhook.add_embed(close_embed)
                close_webhook.execute()
            else:
                for url in webhook_urls:
                    close_webhook = discord_webhook.DiscordWebhook(url=url)
                    close_embed = discord_webhook.DiscordEmbed(
                        title="`Roblox Closed/Crashed`",
                        timestamp=datetime.datetime.now(datetime.timezone.utc))
                    close_embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
                    close_webhook.add_embed(close_embed)
                    close_webhook.execute()

            root.title("Zen [PAUSED]")
            while True:
                if not stopped:
                    root.update()
                else:
                    if not destroyed:
                        root.destroy()
                    sys.exit()
                check = is_roblox_running()
                if check:
                    break
                time.sleep(0.1)
            time.sleep(5)
            latest_log = get_latest_log_file()
            if not latest_log:
                logger.info("No log files found.")
                print("No log files found.")
                return
            with open(latest_log, 'r', encoding='utf-8') as file:
                print(f"Using log file: {latest_log}")
                print()
                logger.info(f"Using log file: {latest_log}")
                root.title("Zen [RUNNING]")
                check_for_hover_text(file)


def open_url(url):
    webbrowser.open(url, new=2, autoraise=True)


def auradetection_toggle_update():
    if aura_detection.get() == 1:
        popup("This feature is EXPERIMENTAL.\nThere are many limitations with aura detection.\n\nIt detects all auras "
              "that get equipped, so if you equip an aura yourself, it will get detected. Additionally, it will only "
              "detect auras that auto-equip.\n\nIt is also incapable of detecting dupes (for example, "
              "rolling Celestial with Celestial already equipped) or Overture: History, for some weird reason.",
              "Warning")
    config.set('Macro', 'aura_detection', str(aura_detection.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def init():
    global roblox_open, started

    if started:
        return

    webhook_field.configure(state="disabled", text_color="gray")
    ps_field.configure(state="disabled", text_color="gray")

    # write new settings to config
    config.set('Webhook', 'webhook_url', webhookURL.get())
    config.set('Webhook', 'private_server', psURL.get())

    # Writing our configuration file to 'example.ini'
    with open(config_name, 'w+') as configfile:
        config.write(configfile)

    # start webhook
    starting_embed = discord_webhook.DiscordEmbed(
        title="`Macro Started`",
        description="> Macro Started\nMacro Version: v1.3.2",
        timestamp=datetime.datetime.now(datetime.timezone.utc))
    starting_embed.set_author(name="Zen", icon_url="https://sleepytil.github.io/biome_thumb/zen.png")
    if multi_webhook.get() != "1":
        if "discord.com" not in webhookURL.get() or "https://" not in webhookURL.get():
            popup("Invalid or missing webhook link.", "Error")
            stop()
            return
        starting_webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
        starting_webhook.add_embed(starting_embed)
        starting_webhook.execute()
    else:
        for url in webhook_urls:
            starting_webhook = discord_webhook.DiscordWebhook(url=url)
            starting_webhook.add_embed(starting_embed)
            starting_webhook.execute()

    started = True

    # start detection
    if is_roblox_running():
        roblox_open = True
        logger.info("Roblox is open.")
        print("Roblox is open.")
        root.title("Zen [RUNNING]")
    else:
        logger.info("Roblox is closed, waiting for Roblox to start...")
        print("Roblox is closed, waiting for Roblox to start...")
        root.title("Zen [PAUSED]")
        while True:
            if not stopped:
                root.update()
            else:
                if not destroyed:
                    root.destroy()
                sys.exit()
            check = is_roblox_running()
            if check:
                break
            time.sleep(0.1)
    time.sleep(5)
    latest_log = get_latest_log_file()
    if not latest_log:
        logger.info(print("No log files found."))
        print("No log files found.")
        return
    with open(latest_log, 'r', encoding='utf-8') as file:
        print(f"Using log file: {latest_log}")
        print()
        logger.info(f"Using log file: {latest_log}")
        root.title("Zen [RUNNING]")
        check_for_hover_text(file)
        for line in file:
            if "[FLog::UpdateController] version response:" in line:
                found_update_version = True
                try:
                    json_data_start = line.find('{"version')
                    if json_data_start != -1:
                        json_data = json.loads(line[json_data_start:])
                        update_version = json_data.get("clientVersionUpload", "")
                        logger.info("Update version found: " + update_version)
                        print("Update version found: " + update_version)
                except:
                    print("Encountered error while parsing JSON to find Roblox update version.")
                    logger.error("Encountered error while parsing JSON to find Roblox update version.")
                    stop()
                if update_version == last_roblox_version and update_version != "":
                    pass
                else:
                    last_roblox_version = update_version
                    # write new version to config
                    config.set('Macro', 'last_roblox_version', last_roblox_version)
                    with open(config_name, 'w+') as configfile:
                        config.write(configfile)
            elif "Local character loaded:" in line and "Incoming MessageReceived Status:" not in line:
                try:
                    _, _, roblox_username = line.partition("Local character loaded: ")
                    roblox_username = roblox_username.strip()
                    logger.info("Username found: " + roblox_username)
                    print("Username found: " + roblox_username)
                    break
                except:
                    print("Encountered error finding username.")
                    logger.error("Encountered error finding username.")
                    stop()


tabview.set("Webhook")

webhook_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Webhook URL:",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20))
webhook_label.grid(column=0, row=0, columnspan=2, padx=(10, 0), pady=(5, 0), sticky="w")

webhook_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                       width=335, textvariable=webhookURL)
webhook_field.grid(row=0, column=1, padx=(144, 0), pady=(10, 0), sticky="w")
if multi_webhook.get() == "1":
    webhook_field.configure(state="disabled", text_color="gray")
    webhookURL.set("Multi-Webhook On")

ps_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Private Server URL:",
                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
ps_label.grid(column=0, row=1, padx=(10, 0), pady=(20, 0), columnspan=2, sticky="w")

ps_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                  width=300, textvariable=psURL)
ps_field.grid(row=1, column=1, padx=(179, 0), pady=(23, 0), sticky="w")

discid_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Discord User ID:",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=20))
discid_label.grid(column=0, row=2, padx=(10, 0), pady=(20, 0), columnspan=2, sticky="w")

discid_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                      width=324, textvariable=discID)
discid_field.grid(row=2, column=1, padx=(155, 0), pady=(23, 0), sticky="w")

# patch_button = customtkinter.CTkButton(root, text="Patch",
#                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
#                                       command=patch_roblox)
# patch_button.grid(row=1, column=3, padx=(5, 0), pady=(10, 0), sticky="w")

start_button = customtkinter.CTkButton(root, text="Start",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=init)
start_button.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), sticky="w")


stop_button = customtkinter.CTkButton(root, text="Stop",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                      command=stop)
stop_button.grid(row=1, column=2, padx=(5, 0), pady=(10, 0), sticky="w")


comet_pfp = customtkinter.CTkImage(dark_image=Image.open("sleepytil.png"), size=(100, 100))
comet_pfp_label = customtkinter.CTkLabel(tabview.tab("Credits"), image=comet_pfp, text="")
comet_pfp_label.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

zen = customtkinter.CTkImage(dark_image=Image.open("zen.png"), size=(100, 100))
zen_label = customtkinter.CTkLabel(tabview.tab("Credits"), image=zen, text="")
zen_label.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="w")

credits_frame = customtkinter.CTkFrame(tabview.tab("Credits"))
credits_frame.grid(row=0, column=2, padx=(10, 0), pady=(10, 0), sticky="w")

comet_label = customtkinter.CTkLabel(credits_frame, text="sleepytil - Creator", font=customtkinter.CTkFont(family="Segoe UI", size=14, weight="bold"))
comet_label.grid(row=0, column=0, padx=(10, 0), sticky="nw")

comet_link = customtkinter.CTkLabel(credits_frame, text="GitHub", font=("Segoe UI", 14, "underline"), text_color="dodgerblue", cursor="pointinghand")
comet_link.grid(row=1, column=0, padx=(10, 0), sticky="nw")
comet_link.bind("<Button-1>", lambda e: open_url("https://github.com/sleepytil"))

sniper_label = customtkinter.CTkLabel(credits_frame, text="Zen", font=customtkinter.CTkFont(family="Segoe UI", size=14, weight="bold"))
sniper_label.grid(row=2, column=0, padx=(10, 0), sticky="nw")

support_link = customtkinter.CTkLabel(credits_frame, text="v1.3.2", font=("Segoe UI", 14))
support_link.grid(row=3, column=0, padx=(10, 0), sticky="nw")
# support_link.bind("<Button-1>", lambda e: open_url("https://discord.gg/solsniper"))

detection_toggle = customtkinter.CTkCheckBox(tabview.tab("Macro"), text="Aura Detection",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                             variable=aura_detection, command=auradetection_toggle_update)
detection_toggle.grid(row=0, column=0, columnspan=2, padx=(10, 0), pady=(10, 0), sticky="w")

detectnotif_toggle = customtkinter.CTkCheckBox(tabview.tab("Macro"), text="Aura Notifications",
                                               font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                               variable=aura_notif, command=auranotif_toggle_update)
detectnotif_toggle.grid(row=1, column=0, columnspan=2, padx=(10, 0), pady=(12, 0), sticky="w")

detectping_toggle = customtkinter.CTkCheckBox(tabview.tab("Macro"), text="Aura Pings",
                                              font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                              variable=aura_ping, command=auraping_toggle_update)
detectping_toggle.grid(row=2, column=0, columnspan=2, padx=(10, 0), pady=(12, 0), sticky="w")

root.bind("<Destroy>", lambda event: x_stop())
root.bind("<Button-1>", lambda e: e.widget.focus_set())

root.mainloop()
