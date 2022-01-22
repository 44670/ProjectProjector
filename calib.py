import ui
import proj
import time


def calibCoax():
    proj.stopInput()
    proj.coaxBegin()
    while True:
        key = ui.waitKey()
        if key == ui.K_UP:
            proj.coaxUp()
        if key == ui.K_DOWN:
            proj.coaxDown()
        if key == ui.K_SPACE:
            proj.coaxNext()
        if key == ui.K_ESCAPE:
            proj.coaxEnd()
            break
    time.sleep(1)
    proj.startInput()


def calibOsci():
    proj.stopInput()
    proj.osciBegin()
    while True:
        key = ui.waitKey()
        if key == ui.K_UP:
            proj.osciUp()
        if key == ui.K_DOWN:
            proj.osciDown()
        if key == ui.K_SPACE:
            proj.osciNext()
        if key == ui.K_ESCAPE:
            proj.osciEnd()
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
