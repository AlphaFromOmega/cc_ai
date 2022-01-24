import math
import time
import asyncio
import keyboard
import pyppeteer
import schedule as s

from directkeys import *

# Client Variables
path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
userPath = "C:\\Users\\mrhat\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Profile 1"
url = "https://orteil.dashnet.org/cookieclicker/"
mousePos = [390, 650]
buildingPos = [2400, 420]
page = None

# Game Variables
cookies = 0
buildings = []


class Building:
    def __init__(self, name, amount, basePrice, cps):
        self.name = name
        self.amount = amount
        self.basePrice = basePrice
        self.cps = cps
        self.value = 0

    def cost(self, multi=1):
        return math.ceil(self.basePrice * pow(1.15, math.factorial(multi) + self.amount - 1))


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
        buildings[i].value = valueNumber(await page.evaluate(f"CookieMonsterData.Objects1['{buildings[i].name}'].colour"))


async def buyBuildings():
    global page, cookies
    for i in range(len(buildings) - 1, -1, -1):
        while buildings[i].value >= 4 and buildings[i].cost() < cookies:
            click(buildingPos[0], buildingPos[1] + 64 * i)
            print(f"Bought 1 {buildings[i].name}")
            time.sleep(0.01)
            buildings[i].amount = await page.evaluate(f"Game.ObjectsById[{i}].amount")
            cookies = await page.evaluate("Game.cookies")
            await updateBuildingValues()


s.every(0.01).seconds.do(clickCookie)


async def main():
    global page, cookies, buildings

    browser = await pyppeteer.launch(headless=False, defaultViewport=None, args=["--start-maximized"], executablePath=path, userDataDir=userPath, profileDirectory="Profile 1")
    page = await browser.newPage()
    await page.goto(url)
    await page.setJavaScriptEnabled(True)
    time.sleep(1)
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
    while True:
        cookies = await page.evaluate("Game.cookies")
        await buyBuildings()
        s.run_pending()
        if keyboard.is_pressed("esc"):
            await browser.close()
            break
        if keyboard.is_pressed("q"):
            printMousePos()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
