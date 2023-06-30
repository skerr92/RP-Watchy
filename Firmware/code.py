
import board, alarm
import time as t_time
from adafruit_datetime import datetime, date, time
import busio, pwmio
import terminalio
import displayio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from digitalio import DigitalInOut, Direction
import adafruit_bus_device.i2c_device as i2c_device

brightness = 5

tft_pwr = DigitalInOut(board.GP21)
tft_pwr.direction = Direction.OUTPUT
tft_pwr.value = True

btn_tl = DigitalInOut(board.GP18)
btn_tl.direction = Direction.INPUT
btn_bl = DigitalInOut(board.GP23)
btn_bl.direction = Direction.INPUT
btn_tr = DigitalInOut(board.GP10)
btn_tr.direction = Direction.INPUT

# rtc clock input

clk_o = DigitalInOut(board.GP11)
clk_o.direction = Direction.INPUT

clk_cnt = 0

# RTC i2c setup

i2c = busio.I2C(board.GP13, board.GP12)

dev = i2c_device.I2CDevice(i2c, 0x68)

def set_rtc_clk_out():
    with dev:
        dev.write(bytes([0x04,0x00]))

def get_rtc_clk_out():
    with dev:
        res = bytearray(1) # sets clock output to 1Hz
        dev.write_then_readinto(bytes([0x04]),res,in_end=1)
        print(int(res[0]))

def get_clk_en():
    with dev:
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x0A]),res,in_end=1)
        print(res[0] & 0xff)

def get_seconds():
    with dev:
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x01]), res, in_end=1)
        return int(res[0])

def get_minute():
    with dev:
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x02]), res, in_end=1)
        return int(res[0])

def get_hour():
    with dev:
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x03]), res, in_end=1)
        return int(res[0])

def set_freq_comp(val):
    with dev:
        dev.write(bytes([0x08,val]))

def set_seconds(secs):
    with dev:
        dev.write(bytes([0x01,secs]))
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x01]), res, in_end=1)
        #print("seconds: ", res[0])

def set_minute(min):
    with dev:
        int(min)
        dev.write(bytes([0x02,min]))
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x02]), res, in_end=1)
        #print("minutes: ", res[0])

def set_hour(hr):
    with dev:
        dev.write(bytes([0x03,hr]))
        res = bytearray(1)
        dev.write_then_readinto(bytes([0x03]), res, in_end=1)
        #print("hours: ", res[0])
# Release any resources currently in use for the displays
displayio.release_displays()

spi = busio.SPI(board.GP2, MOSI=board.GP3, MISO=None)
tft_cs = board.GP1
tft_dc = board.GP4

bl = pwmio.PWMOut(board.GP5, frequency=100, duty_cycle=int(brightness * 2 * 65535 / 100))

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=board.GP0
)

year = 2022
month = 12
day = 30
c_date = date(year,month,day)

hour = get_hour() % 12
if (hour == 0):
    hour = 12
minute = get_minute() % 60
second = 0
#print("minute from RTC: ", minute)
#print("hour from RTC: ", hour)
c_time = time(hour, minute)
#set_freq_comp(255)
display = ST7789(display_bus, width=240, height=240, rowstart=80, rotation=180)

# Make the display context
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(240, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x00FF00  # Bright Green

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(200, 200, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Purple
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=20, y=20)
splash.append(inner_sprite)

# Draw a label
text_group = displayio.Group(scale=2, x=50, y=90)
text = str(c_time)
tg2 = displayio.Group(scale=4, x=70, y=140)
t2 = "SETH"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00)
t2_area = label.Label(terminalio.FONT, text=t2, color=0x00FF00)
text_group.append(text_area)  # Subgroup for text scaling
tg2.append(t2_area)
splash.append(text_group)
splash.append(tg2)

disp_on = True
ret_time = 0
time_set_mode = 0
screen_time_on = 0
set_rtc_clk_out()
t_time.sleep(0.1)
get_rtc_clk_out()

while True:
    if btn_tr.value == 0 and btn_bl.value and btn_tl.value:
        if disp_on:
            bl.duty_cycle = int(brightness * 2 * 65535 / 100)  # Up
            tft_pwr.value = True
            disp_on = False
            t_time.sleep(1)
        elif disp_on == 0:
            bl.duty_cycle = 0  # Down
            tft_pwr.value = False
            disp_on = True
            t_time.sleep(1)

    while btn_tr.value == 0 and btn_tl.value == 0 and btn_bl.value:
        if brightness != 50:
            brightness = brightness + 5
            text_group.scale = 2
            text_area.text = "Brightness: " + str(brightness)
            t_time.sleep(0.25)
        elif brightness == 50:
            brightness = 50
            text_group.scale = 2
            text_area.text = "Max Brightness"
            t_time.sleep(0.25)
        bl.duty_cycle = int(brightness * 2 * 65535 / 100)

    while btn_tr.value == 0 and btn_bl.value == 0 and btn_tl.value:
        if brightness == 0:
            brightness = 0
        elif brightness > 0:
            text_group.scale = 2
            text_area.text = "Brightness: " + str(brightness)
            t_time.sleep(0.25)
            brightness = brightness - 5
        bl.duty_cycle = int(brightness * 2 * 65535 / 100)

    while not btn_bl.value and btn_tl.value and btn_tr.value and time_set_mode < 2:
        time_set_mode = time_set_mode + 1
        t_time.sleep(1)

    while time_set_mode == 2:
        tg2.scale = 3
        tg2.x = 35
        t2_area.text = "set time"
        if btn_tl.value == 0:
            ret_time = 0
            if hour < 12:
                hour = hour + 1
            elif hour == 12:
                hour = 1
            t_time.sleep(0.25)
        if btn_tr.value == 0:
            ret_time = 0
            if minute < 59:
                minute = minute + 1
            elif minute == 59:
                minute = 0
            t_time.sleep(0.25)
        c_time = time(hour, minute)
        set_minute(minute)
        set_hour(hour)
        text_area.text = str(c_time)
        while btn_tl.value and btn_tr.value and ret_time < 5:
            ret_time = ret_time + 1
            t_time.sleep(1)
            c_time = time(hour, minute, second)

        if ret_time == 5:
            tg2.scale = 4
            tg2.x = 70
            t2_area.text = "SETH"
            time_set_mode = 0
    ret_time = 0
    text_group.scale = 3
    text_area.text = str(c_time)
    t_time.sleep(0.97)

    clk_cnt = 0
    if second < 59:
        second = second + 1
        #set_seconds(second)
    elif second == 59:
        second = 0
        set_seconds(second)
        if minute < 59:
            minute = minute + 1
            set_minute(minute)
        elif minute == 59:
            minute = 0
            set_minute(minute)
            if hour < 12:
                hour = hour + 1
                set_hour(hour)
            elif hour == 12:
                hour = 1
                set_hour(hour)

    #hour = get_hour() % 12
    #if (hour == 0):
    #    hour = 12
    #minute = get_minute() % 60
    #second = get_seconds() % 60
    c_time = time(hour, minute,second%60)
