try:
    import serial
except:
    try:
        import os
        os.system("pip install pyserial")
        import serial
    except:
        raise Exception("pyserial ist nicht installiert und konnte nicht automatisch installiert werden. Bitte mit 'pip install pyserial' installieren")

import time

class Hardware:

    def __init__(self, port, baudrate=115200, timeout=0.0005):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.board = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def check_input(self):
        """
        returns 3 variables:
        l: true when left button pressed
        r: true when right button pressed
        power: 1-10 power of plunger, 0 when nothing detected
        """
        l = False
        r = False
        power = 0
        
        ReceivedString = str(self.board.readline())
        if ReceivedString != "b''":
            ReceivedString = ReceivedString[2:-5]
            try:
                power = int(ReceivedString)
                if power < 0:
                    power = 0
                if power > 10:
                    power = 10
            except:
                letter = ReceivedString
                if letter == "L":
                    l = True
                if letter == "R":
                    r = True

        return l, r, power
    
    def display(self, score, highscore):
        """
        sends score(int, maximum 4 digits) and highscore(int, maximum 4 digits) to display
        !!! needs some time after init so the display is fully ready.
        !!! 3s after init and 2s between 2 calls of the function
        """
        score = str(int(score))
        highscore = str(int(highscore))
        highscore = (4-len(highscore))*"0" + highscore
        if ((len(score) > 4) or (len(highscore) > 4)):
            raise Exception("Ah ah ah. Da passt was nicht. Da dürfen maximal 4 stellige zahlen hin.")
        combined = score +","+ highscore
        send = combined.encode()
        self.board.write(send)


if __name__ == "__main__":
    com_port = "/dev/ttyACM0" # !!!WICHTIG!!! Muss je nach PC, BEtriebssystem und Port geändert werden.

    hardware1 = Hardware(com_port, 115200, 0.0005)
    '''
    while True:
        l, r, power = hardware1.check_input()
        if power != 0:
            print(l, r, power)

    '''
            
    
    time.sleep(3)
    hardware1.display(678, 14)
    time.sleep(3)
    hardware1.display(9999, 1234)
    time.sleep(3)
    hardware1.display(9999, 9999)
    time.sleep(10)