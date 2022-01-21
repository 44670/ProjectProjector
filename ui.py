print("Initializing UI...")
import pygame
import pygame.freetype
import pygame.image
from pygame.locals import *
from lang_cn import TR
import sys
import time
import proj

FONT_PATH = 'font.ttf'

SCREEN_H = 720
SCREEN_W = 1280

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

COLOR_BG = BLACK
COLOR_FG = WHITE
COLOR_MENU_SEL = (24, 242, 192)
COLOR_LINE = (127, 127, 127)

pygame.display.init()
pygame.freetype.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), 0, 32)
basicFont = pygame.freetype.Font(FONT_PATH, 48)
basicFontHeight = basicFont.get_sized_height()
itemHeight = basicFontHeight + 10

screen.fill(BLACK)
pygame.display.update()

laserImg = None
laserImg = pygame.image.load('laser.png')

def pollGpioKey():
    return None

def pollKey():
    while True:
        event = pygame.event.poll()
        if event.type == NOEVENT:
            return pollGpioKey()
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYUP:
            return event.key


def waitKey(timeout=None):
    timePassed = 0
    while True:
        evt = pollKey()
        if (evt != None):
            return evt
        time.sleep(0.01)
        timePassed += 10
        if (timeout != None) and (timePassed >= timeout):
            return None

def flushKey():
    while waitKey(200) != None:
        pass

def handlePowerButton():
    print('---power button pressed---')

def updateScreen():
    pygame.display.update()

def drawText(x, y, text, colorFg, colorBg):
    return basicFont.render_to(screen, (x, y), text, colorFg, colorBg)

def drawTextMultiline(x, y, text, colorFg, colorBg):
    for line in text.split(u'\n'):
        basicFont.render_to(screen, (x, y), line, colorFg, colorBg)
        y += itemHeight

def clearAndDrawTitle(title):
    screen.fill(COLOR_BG)
    screen.fill(COLOR_FG, (0, itemHeight - 3, SCREEN_W, 2))
    drawText(10, 5, title, COLOR_FG, COLOR_BG)

def renderMessageBox(title, msg):
    clearAndDrawTitle(TR(title))
    drawTextMultiline(30, itemHeight + 10, TR(msg), COLOR_FG, COLOR_BG)
    updateScreen()


def drawBorder(x, y, w, h, borderWidth, borderColor):
    screen.fill(borderColor, (x, y, w, borderWidth))
    screen.fill(borderColor, (x, y + h - borderWidth, w, borderWidth))
    screen.fill(borderColor, (x, y, borderWidth, h))
    screen.fill(borderColor, (x + w - borderWidth, y, borderWidth, h))

SWKBD_MAP = [None] * 3
SWKBD_MAP[0] = '1234567890abcdefghijklmnopqrstuvwxyz'
SWKBD_MAP[1] = SWKBD_MAP[0].upper()
SWKBD_MAP[2] = r"""~`@#$%^&*+-_=<>()[]{}\|/;:'",.?!    """
SWKBD_FUNC = ['<-', '[ ]', 'Aa.', 'OK']

def inputDialog(title, text):
    KBD_GRID_SIZE = 80
    kbdMode = 0
    kbdSelection = 0
    if text == None:
        text = ''
    while True:
        clearAndDrawTitle(TR(title))
        drawText(30, itemHeight + 10, text + '_', COLOR_FG, COLOR_BG)
        drawBorder(0, itemHeight, SCREEN_W, itemHeight, 2, COLOR_FG)
        for i in range(0, 40):
            if i < 36:
                t = SWKBD_MAP[kbdMode][i]
            else:
                t = SWKBD_FUNC[i - 36]
            x = KBD_GRID_SIZE * (i % 10)
            y = SCREEN_H - (KBD_GRID_SIZE * (4 - i // 10))
            drawText(x + 10, y + 10, t, COLOR_FG, COLOR_BG)
            if kbdSelection == i:
                drawBorder(x, y, KBD_GRID_SIZE, KBD_GRID_SIZE, 3, COLOR_MENU_SEL)
        updateScreen()
        key = waitKey()
        if key == K_DOWN:
            kbdSelection += 10
        elif key == K_UP:
            kbdSelection -= 10
        elif key == K_LEFT:
            kbdSelection -= 1
        elif key == K_RIGHT:
            kbdSelection += 1
        elif key == K_ESCAPE:
            return None
        elif (key == K_RETURN) or (key == K_SPACE):
            if kbdSelection == 36:
                text = text[:-1]
            elif kbdSelection == 37:
                text += ' '
            elif kbdSelection == 38:
                kbdMode += 1
            elif kbdSelection == 39:
                return text
            else:
                text += SWKBD_MAP[kbdMode][kbdSelection]

        kbdMode %= len(SWKBD_MAP)
        if kbdSelection < 0:
            kbdSelection = 40 + kbdSelection
        kbdSelection %= 40

def msgBox(title, text):
    renderMessageBox(title, text)
    waitKey()

def drawWarning(x=0, y=0):
    screen.blit(laserImg, (x, y))
    x += 160
    basicFont.render_to(screen, (x, y), u'警告：本设备为Class 3R激光设备，错误使用可能导致永久性视力损害。', COLOR_FG, COLOR_BG, size=35)
    y += 50
    basicFont.render_to(screen, (x, y), u'请勿直视本设备发出的激光光束，更不能将激光指向自己或其他人。', COLOR_FG, COLOR_BG, size=35)
    y += 50
    basicFont.render_to(screen, (x, y), u'儿童必须在家长监护下使用本设备。', COLOR_FG, COLOR_BG, size=35)
    y += 50
    basicFont.render_to(screen, (x, y), u'机身绿色指示灯亮时请勿移除电源。', COLOR_FG, COLOR_BG, size=35)



def showMenu(items, caption, selectTo=None, style=None):
    caption = TR(caption)

    itemPerPage = SCREEN_H // (itemHeight) - 2
    selBorder = 4
    menuRect = (0, basicFontHeight, SCREEN_W, SCREEN_H - basicFontHeight * 2)
    menuSel = 0

    if len(items) == 0:
        renderMessageBox(caption, '-- No Items --')
        key = waitKey()
        return -1, None

    if selectTo != None:
        if selectTo >= 0:
            menuSel = selectTo
    while True:
        if (menuSel >= len(items)):
            menuSel = 0
        if (menuSel < 0):
            menuSel = len(items) - 1
        menuStart = (menuSel // itemPerPage) * itemPerPage
        clearAndDrawTitle(caption)
        x = 30
        y = itemHeight

        for i in range(menuStart, min(menuStart + itemPerPage, len(items))):
            drawText(x, y + 10, TR(items[i]), COLOR_FG, COLOR_BG)
            if menuSel == i:
                drawBorder(0, y, SCREEN_W, itemHeight,
                           selBorder, COLOR_MENU_SEL)
            screen.fill(COLOR_LINE, (0, y + itemHeight - 1, SCREEN_W, 1))
            y += itemHeight

        if len(items) > itemPerPage:
            drawText(SCREEN_W - 200, y + 10, 'Page %d/%d' % (menuSel // itemPerPage +
                                                         1, (len(items) - 1) // itemPerPage + 1), COLOR_FG, COLOR_BG)
        if style == 'main':
            drawWarning(10, 530)
        updateScreen()

        key = waitKey()
        
        if (key == K_DOWN):
            menuSel += 1
        elif key == K_UP:
            menuSel -= 1
        elif (key == K_RETURN) or (key == K_RIGHT) or (key == K_LEFT) or (key == K_SPACE):
            return menuSel, key
        elif key == K_ESCAPE:
            return -1, key
        elif key == K_F1:
            handlePowerButton()
  