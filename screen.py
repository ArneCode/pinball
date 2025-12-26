"""
Screen stuff, can be disabled by setting USE_MENUE to False
"""
import pygame
res = (720,720)  
    
fpsClock = pygame.time.Clock()
fps = 60
pygame.init()
font = pygame.font.SysFont('Arial', 40)

class ScreenHandler():
    def __init__(self, screen_list):
        self.screen_list = screen_list
    def update(self, screen):
        for screenobj in self.screen_list:
            screenobj.ScreenUpdate(screen)
            if screenobj.checkState():
                screenobj.DrawButton(screen)

        

    def handle_event(self, event):
        for screenobj in self.screen_list:
            if screenobj.checkState():
                
                for screenbutton in screenobj.button_list:
                    if screenbutton.process(event):
                        print("screenbutton pressed")
                        
                        screenobj.endScreen()

                        screenbutton.button_function()
                        
                        for screen in self.screen_list:
                            if screen.checkState():
                                print(f"screen: {screen}")



class Screen():
    def __init__(self, title, on_update = None , width = 720, height = 720, color = None):
        self.on_update = on_update
        self.title = title
        self.width = width
        self.height = height
        self.color = color
        self.State = False #If the screen is shown or not
    def setButtons(self, button_list):
        self.button_list = button_list
    def makeScreen(self):
        pygame.display.set_caption(self.title)
        self.State = True
        print("activating screen")
        #self.screen = pygame.display.set_mode((self.width, self.height))
        #self.screen = pygame.display.set_mode((self.width, self.height))
    def endScreen(self):
        print("end screen")
        self.State = False
    def checkState(self): #why is the color there
        #self.color = color
        #print(f"checked, got {self.State}")
        return self.State
    def ScreenUpdate(self, screen):
       # print(f"{self.State}")
        if self.State and self.color is not None:
            #print(f"The Menu is filled")
            screen.fill(self.color)
    def DrawButton(self, screen, score = 0):
        """
        Name ist nicht ganz richtig, malt nicht nur button sondern auch score oder highscore
        """
        for button in self.button_list:
            button.draw(screen) #ich bin mir nicht sicher ob das so richtig ist
        #pygame.draw.rect(screen, (255,0,0), pygame.Rect(100, 100, 100, 100))
        #scoreSurf = font.render(f"Your score is: {str(score)}", True, (0, 255, 0))
        #screen.blit(scoreSurf, (00, 0))
        
    
    def runFunction(self, screen):
        print("run_function")
        return self.on_update(screen)




class Button ():
    def __init__(self, x, y, width, height, button_function, button_text = "Button"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.button_text = button_text
        self.button_function = button_function
        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        
        
        #objects.append(self)
    def draw(self, surface):
        pygame.draw.rect(surface, (255,0,0),self.buttonRect)
        self.buttonSurf = font.render(self.button_text, True, (20, 20, 20))
        surface.blit(self.buttonSurf, (self.x, self.y)) 

    def process(self, event):
        #print("process")
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            #print(f"mousebttndown {mouse_pos}")
            if self.x  <= mouse_pos[0] and mouse_pos[0] <= self.x + self.width and self.y < mouse_pos[1] and mouse_pos[1] < self.y + self.height:
                return True
                #game()
            else:
                return False