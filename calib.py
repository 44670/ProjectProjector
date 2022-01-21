import ui
import proj
import time


def calibCoax():
    proj.stopInput()
    proj.sendCmd(0x32)
    while True:
        key = ui.waitKey()
        if key == ui.K_UP:
            proj.sendCmd(0x34)
        if key == ui.K_DOWN:
            proj.sendCmd(0x33)
        if key == ui.K_SPACE:
            proj.sendCmd(0x32)
        if key == ui.K_ESCAPE:
            proj.sendCmd(0x35, [0])
            break
    time.sleep(1)
    proj.startInput()


def calibOsci():
    proj.stopInput()
    proj.sendCmd(0x36)
    while True:
        key = ui.waitKey()
        if key == ui.K_UP:
            proj.sendCmd(0x38)
        if key == ui.K_DOWN:
            proj.sendCmd(0x37)
        if key == ui.K_SPACE:
            proj.sendCmd(0x36)
        if key == ui.K_ESCAPE:
            proj.sendCmd(0x39, [0])
            break
    time.sleep(1)
    proj.startInput()


def calib():
    ui.clearAndDrawTitle("Calib")
    ui.updateScreen()
 while True:
      key = ui.waitKey()
       if key == ui.K_1:
            calibCoax()
        if key == ui.K_2:
            calibOsci()
        if key == ui.K_RETURN:
            break
