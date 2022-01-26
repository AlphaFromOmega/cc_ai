import math
import time
import asyncio
import keyboard
import pyppeteer
import schedule

from directkeys import *

# Client Variables
path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
userPath = "C:\\Users\\mrhat\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Profile 1"
url = "https://orteil.dashnet.org/cookieclicker/"
game_pos = [0, 70]
mousePos = [390, 650]
buildingPos = [2400, 350]
upgradePos = [2275, 275]
page = None
upgrade_check = 0
click_check = 0
ai_enabled = True

# Game Variables
cookies = 0
buildings = []
upgrades = []


class Building:
    def __init__(self, name, amount, basePrice, cps):
        self.name = name
        self.amount = amount
        self.basePrice = basePrice
        self.cps = cps
        self.value = 0

    def cost(self, multi=1):
        return math.ceil(self.basePrice * pow(1.15, math.factorial(multi) + self.amount - 1))


class Upgrades:
    def __init__(self, name, unlocked, bought, basePrice, order):
        self.name = name
        self.unlocked = bool(unlocked)
        self.bought = bool(bought)
        self.basePrice = basePrice
        self.order = order
        self.value = 0

    def __repr__(self):
        return f"Upgrade({self.name}: {self.unlocked}, {self.bought}, {self.basePrice}, {self.order}, {self.value})"

    def __lt__(self, other):
        return self.basePrice < other.basePrice

    def getTechName(self):
        tn = self.name.replace("\"", "\\\"")
        return tn


class GoldenCookie:
    def __init__(self, wrath, x, y):
        self.wrath = wrath
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Upgrade({self.name}: {self.unlocked}, {self.bought}, {self.basePrice}, {self.order}, {self.value})"

    def __lt__(self, other):
        return self.basePrice < other.basePrice

    def getTechName(self):
        tn = self.name.replace("\"", "\\\"")
        return tn


def printMousePos():
    print(f"{queryMousePosition().x}, {queryMousePosition().y}")


def clickCookie():
    click(mousePos[0], mousePos[1])


def valueNumber(value):
    if value == "Blue":
        return 5
    if value == "Green":
        return 4
    if value == "Yellow":
        return 3
    if value == "Orange":
        return 2
    if value == "Red":
        return 1
    if value == "Purple":
        return 0
    if value == "Gray":
        return -1


async def updateBuildingValues():
    for i in range(len(buildings)):
        buildings[i].amount = await page.evaluate(f"Game.ObjectsById[{i}].amount")
        buildings[i].value = valueNumber(await page.evaluate(f"CookieMonsterData.Objects1['{buildings[i].name}'].colour"))
        if buildings[i].value == 4:
            print(f"Best valued building is {buildings[i].name}")


async def buyBuildings():
    global page, cookies
    for i in range(len(buildings) - 1, -1, -1):
        while buildings[i].value >= 4 and buildings[i].cost() < cookies:
            click(buildingPos[0], buildingPos[1] + 64 * i)
            print(f"Bought 1 {buildings[i].name} for {buildings[i].cost()}")
            time.sleep(0.01)
            buildings[i].amount = await page.evaluate(f"Game.ObjectsById[{i}].amount")
            cookies = await page.evaluate("Game.cookies")
            await updateBuildingValues()


async def updateUpgrades():
    global page, upgrades
    available_upgrades = []
    j = 0
    for i in range(len(upgrades)):
        upgrades[i].unlocked = await page.evaluate(f"Game.Upgrades[\"{upgrades[i].getTechName()}\"].unlocked")
        upgrades[i].bought = await page.evaluate(f"Game.Upgrades[\"{upgrades[i].getTechName()}\"].bought")
        if not upgrades[i].bought and upgrades[i].unlocked and await page.evaluate(f"typeof CookieMonsterData.Upgrades[\"{upgrades[i].getTechName()}\"] !== 'undefined'"):
            available_upgrades.append(0)
            available_upgrades[j] = upgrades[i]
            available_upgrades[j].value = valueNumber(await page.evaluate(f"CookieMonsterData.Upgrades[\"{upgrades[i].getTechName()}\"].colour"))
            j += 1
    return available_upgrades


def upgradeKey(e):
    return e["order"]


async def buyUpgrades():
    global cookies
    moveMouseTo(upgradePos[0], upgradePos[1])
    au = await updateUpgrades()
    base_value = -1
    while True:
        if au[0].basePrice > cookies:
            break
        for i in range(len(au)):
            print(f"Checking Upgrade:({au[i]})")
            if au[i].basePrice <= cookies:
                if au[i].value == base_value:
                    click(upgradePos[0] + (i % 5) * 64, upgradePos[1] + math.floor(i / 5) * 64)
                    print(f"Bought Upgrade:({au[i]})")
                    cookies = await page.evaluate("Game.cookies")
                    au.remove(au[i])
                    i -= 1
                    for j in range(len(au)):
                        print(f"Revaluing Upgrade:({au[j]})")
                        au[j].value = valueNumber(await page.evaluate(f"CookieMonsterData.Upgrades[\"{au[j].getTechName()}\"].colour"))
            else:
                break;
        if base_value == -1:
            base_value = 5
        else:
            base_value -= 1
        if not (base_value > 3):
            break;

    await updateBuildingValues()


async def clickGoldenCookies():
    golden_cookie = []
    shimmers = await page.evaluate("Game.shimmers.length")
    if shimmers > 0:
        print("Found Golden Cookie")
        for i in range(shimmers):
            golden_cookie.append(0)
            golden_cookie[i] = GoldenCookie(
                await page.evaluate(f"Game.shimmers[{i}].wrath"),
                await page.evaluate(f"Game.shimmers[{i}].x"),
                await page.evaluate(f"Game.shimmers[{i}].y")
            )
        for i in golden_cookie:
            if not i.wrath:
                click(game_pos[0] + i.x + 50, game_pos[1] + i.y + 50)


async def mouseControls():
    global upgrade_check
    await clickGoldenCookies()
    await buyBuildings()
    if time.time() - upgrade_check > 10:
        await buyUpgrades()
        upgrade_check = time.time()
    clickCookie()


async def main():
    global page, cookies, buildings, upgrades, ai_enabled, click_check
    mp = None

    browser = await pyppeteer.launch(headless=False, defaultViewport=None, args=["--start-maximized"], executablePath=path, userDataDir=userPath, profileDirectory="Profile 1")
    page = await browser.newPage()
    await page.goto(url)
    await page.setJavaScriptEnabled(True)
    time.sleep(1)
    click(2537, 92)
    await page.evaluate("Game.LoadMod('https://cookiemonsterteam.github.io/CookieMonster/dist/CookieMonster.js');")
    time.sleep(1)
    max_buildings = await page.evaluate("Game.ObjectsById.length")
    for i in range(max_buildings):
        buildings.append(0)
        buildings[i] = Building(
            await page.evaluate(f"Game.ObjectsById[{i}].name"),
            await page.evaluate(f"Game.ObjectsById[{i}].amount"),
            await page.evaluate(f"Game.ObjectsById[{i}].basePrice"),
            await page.evaluate(f"Game.ObjectsById[{i}].cps")
        )
        buildings[i].value = valueNumber(await page.evaluate(f"CookieMonsterData.Objects1['{buildings[i].name}'].colour"))
        await buyBuildings()
    max_upgrades = await page.evaluate(f"Game.UpgradesById.length")
    for i in range(max_upgrades):
        upgrades.append(0)
        upgrades[i] = Upgrades(
            await page.evaluate(f"Game.UpgradesById[{i}].name"),
            await page.evaluate(f"Game.UpgradesById[{i}].unlocked"),
            await page.evaluate(f"Game.UpgradesById[{i}].bought"),
            await page.evaluate(f"Game.UpgradesById[{i}].basePrice"),
            await page.evaluate(f"Game.UpgradesById[{i}].order")
        )
    upgrades.sort()
    print(upgrades)
    while True:
        cookies = await page.evaluate("Game.cookies")
        if ai_enabled and time.time() - click_check > 0.01:
            await mouseControls()
            click_check = time.time() - click_check
        if keyboard.is_pressed("ctrl+space"):
            ai_enabled = not ai_enabled
        if keyboard.is_pressed("esc"):
            click(835, 125)
            time.sleep(0.2)
            click(820, 350)
            time.sleep(0.2)
            await browser.close()
            break
        if keyboard.is_pressed("q"):
            if mp != queryMousePosition():
                printMousePos()
                mp = queryMousePosition()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
