# game.py
import pygame
import sys
import random

# Importa le classi manager
from champions import get_available_champions, Champion
from shop import ShopManager
from battle import BattleManager

# Importa TUTTE le costanti e le utility da config.py
from config import (
    WIDTH, HEIGHT, WHITE, BLUE, LIGHT_BLUE, 
    GREEN, RED, GOLD, TITLE_FONT, BUTTON_FONT, TEXT_FONT, draw_text
)

# --- Inizializzazione Audio ---
# #pygame.mixer.init()
# try:
#     pygame.mixer.music.load("audio/battle_music.mp3")
#     pygame.mixer.music.set_volume(0.7)
#     attack_sound = pygame.mixer.Sound("audio/attack.wav")
#     attack_sound.set_volume(0.1)
# except Exception as e:
#     print(f"Errore caricamento audio: {e}")
#     attack_sound = None

# --- Inizializzazione Pygame ---
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini TFT - by andreazapp-dev")


# --- CLASSE PRINCIPALE DEL GIOCO ---

class Game:
    """
    Gestisce lo stato generale del gioco (Menu, Shop, Battle),
    i dati del giocatore e il ciclo di gioco principale.
    """
    def __init__(self):
        self.screen = SCREEN
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.game_state = "MAIN_MENU"
        
        self.champions_database = get_available_champions() 
        
        # Dati persistenti del Giocatore
        self.player_gold = 20
        self.player_hp = 100
        self.player_level = 1
        self.board_slots = 3 
        self.bench_slots = 5 
        self.board = [] 
        self.bench = []
        self.round_number = 1
        
        # Manager di gioco
        self.shop_manager = ShopManager(self, self.champions_database) # <-- Aggiungi database
        self.battle_manager = None
        
        # Variabile per tenere traccia del vincitore dell'ultima battaglia
        self.last_battle_winner = None

    def run(self):
        """ Il loop di gioco principale, non bloccante. """
        
        # if not pygame.mixer.music.get_busy():
        #     try:
        #         pygame.mixer.music.play(-1)
        #     except Exception as e:
        #         print(f"Errore play musica: {e}")
            
        while self.running:
            # 1. Gestisci Eventi
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    
                if self.game_state == "MAIN_MENU":
                    self.handle_menu_events(event)
                elif self.game_state == "SHOP":
                    self.shop_manager.handle_event(event)
                elif self.game_state == "BATTLE" and self.battle_manager:
                    self.battle_manager.handle_event(event)
                elif self.game_state == "RESULT":
                    self.handle_result_events(event)

            # 2. Aggiorna Logica
            if self.game_state == "BATTLE" and self.battle_manager:
                self.battle_manager.update()
                if self.battle_manager.is_over:
                    self.end_battle(self.battle_manager.winner)

            # 3. Disegna (Render)
            self.screen.fill((20, 20, 20))
            
            if self.game_state == "MAIN_MENU":
                self.draw_main_menu()
            elif self.game_state == "SHOP":
                self.shop_manager.draw(self.screen)
            elif self.game_state == "BATTLE" and self.battle_manager:
                self.battle_manager.draw(self.screen)
            elif self.game_state == "RESULT":
                self.draw_result_screen()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    # --- Gestione Stato: MAIN_MENU ---
    def draw_main_menu(self):
        draw_text("MINI TFT", TITLE_FONT, BLUE, self.screen, WIDTH // 2, HEIGHT // 3)
        draw_text("by andreazapp-dev", TEXT_FONT, (180, 180, 180),
                  self.screen, WIDTH // 2, HEIGHT // 3 + 60)

        # Salva il rect del bottone per il controllo click
        self.play_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 70)
        pygame.draw.rect(self.screen, LIGHT_BLUE, self.play_button_rect, border_radius=10)
        draw_text("GIOCA", BUTTON_FONT, WHITE, self.screen, WIDTH // 2, HEIGHT // 2 + 35)

    def handle_menu_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Assicurati che play_button_rect esista
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                self.game_state = "SHOP"
                # Resettiamo i dati del giocatore per una nuova partita
                self.player_gold = 20
                self.player_hp = 100
                self.board = [] # Board vuoto
                self.bench = [] # Panchina vuota
                self.shop_manager.reset() # Ricarica lo shop
                self.round_number = 1   

    # --- Gestione Stato: BATTLE ---
    def start_battle(self):
        print(f"--- INIZIO ROUND {self.round_number} ---")
        print("Avvio battaglia con:", [c.name for c in self.board])
        
        enemy_team_to_battle = []
        
        for _ in range(3): # Scegli 3 nemici
            # Usa il database che abbiamo già caricato
            base_champ = random.choice(self.champions_database) # <-- Modifica qui
            
            if random.random() < 0.10: 
                print(f"Nemico potenziato: {base_champ.name} Lvl 2!")
                upgraded = Champion(
                    base_champ.name, 
                    int(base_champ.hp * 1.6), 
                    int(base_champ.attack * 1.6), 
                    base_champ.image_path,
                    int(getattr(base_champ, 'defense', 0) * 1.6),
                    getattr(base_champ, 'crit_chance', 0.1),
                    # Copiamo TUTTI i dati base, inclusi sprite!
                    getattr(base_champ, 'mana_max', 100),
                    getattr(base_champ, 'mana_start', 0),
                    getattr(base_champ, 'attack_speed', 0.7),
                    getattr(base_champ, 'attack_range', 1),
                    # getattr(base_champ, 'sprite_path', None), 
                    # getattr(base_champ, 'sprite_offset_y', 0)
                )
                upgraded.level = 2
                upgraded.max_hp = upgraded.hp
                enemy_team_to_battle.append(upgraded)
            else:
                enemy_team_to_battle.append(base_champ)
        
        # Passa il database anche al BattleManager
        self.battle_manager = BattleManager(self.board, enemy_team_to_battle, self.champions_database) # <-- Aggiungi database
        self.game_state = "BATTLE"

    def end_battle(self, winner):
        # pygame.mixer.music.stop()
        self.last_battle_winner = winner
        self.game_state = "RESULT"
        
        # Logica ricompense: 5 gold base, +3 per la vittoria
        base_gold = 5
        win_gold = 3
        
        if winner == "player":
            gold_earned = base_gold + win_gold
            self.player_gold += gold_earned
            print(f"Vittoria! Oro: {self.player_gold} (+{gold_earned})")
        else:
            gold_earned = base_gold
            self.player_gold += gold_earned
            self.player_hp -= 10 # Danno al giocatore
            print(f"Sconfitta! Oro: {self.player_gold} (+{gold_earned}), HP: {self.player_hp}")
        
        # Incrementa il round
        self.round_number += 1
        
        # Ricarica gratuita dello shop per il prossimo round
        self.shop_manager.roll_shop(is_free=True)
        
        if self.player_hp <= 0:
            print("Sei stato sconfitto! GAME OVER")
            # Se il giocatore perde, lo rimandiamo al menu principale
            self.game_state = "MAIN_MENU"
            
    # --- Gestione Stato: RESULT ---
    def draw_result_screen(self):
        text = "🏆 Vittoria!" if self.last_battle_winner == "player" else "💀 Sconfitta..."
        color = GREEN if self.last_battle_winner == "player" else RED
        draw_text(text, TITLE_FONT, color, self.screen, WIDTH // 2, HEIGHT // 2)
        draw_text("Clicca per continuare...", TEXT_FONT, WHITE, self.screen, WIDTH // 2, HEIGHT // 2 + 80)

    def handle_result_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.play(-1)
                except Exception as e:
                    print(f"Errore play musica: {e}")
            self.game_state = "SHOP"


#--- AVVIO DEL GIOCO ---
if __name__ == "__main__":
    game = Game()
    game.run()