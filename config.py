# config.py
import pygame

# Inizializza solo i moduli che servono (font)
# pygame.init() verrà chiamato in game.py
pygame.font.init() 

# --- Costanti di Gioco ---
WIDTH, HEIGHT = 1400, 900

# --- Colori ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 120, 215)
LIGHT_BLUE = (0, 150, 255)
GRAY = (50, 50, 50)
GREEN = (60, 200, 100)
RED = (200, 60, 60)
GOLD = (230, 180, 30)

# --- Font ---
# (Questi ora vengono caricati qui una sola volta)
try:
    TITLE_FONT = pygame.font.Font(None, 80)
    BUTTON_FONT = pygame.font.Font(None, 50)
    TEXT_FONT = pygame.font.Font(None, 30)
except Exception as e:
    print(f"Errore caricamento font: {e}")
    # Fallback in caso di errore
    TITLE_FONT = pygame.font.SysFont("Arial", 80)
    BUTTON_FONT = pygame.font.SysFont("Arial", 50)
    TEXT_FONT = pygame.font.SysFont("Arial", 30)


# --- Funzione Utile (Utility) ---
def draw_text(text, font, color, surface, x, y, center=True):
    """ Funzione helper per disegnare testo centrato o allineato a sinistra. """
    try:
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        surface.blit(text_obj, text_rect)
    except Exception as e:
        print(f"Errore in draw_text: {e}")