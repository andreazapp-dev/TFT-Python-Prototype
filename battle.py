# battle.py
import pygame
import random
import copy
import math

# Importiamo da config.py
from config import draw_text, TEXT_FONT, GREEN, RED, BLUE, BLACK, WHITE

# Importiamo la classe Champion aggiornata
from champions import Champion, SPRITE_SIZE

class BattleManager:
    """
    Gestisce la logica e il rendering della battaglia IN TEMPO REALE.
    """
    def __init__(self, player_team_base, enemy_team_base, champions_database):
        # self.attack_sound = attack_sound
        self.champions_database = champions_database
        
        # --- Copia i Campioni ---
        # Creiamo copie da battaglia con la nuova logica
        self.player_team = self.create_battle_copies(player_team_base)
        self.enemy_team = self.create_battle_copies(enemy_team_base)
        self.all_champs = self.player_team + self.enemy_team

        # --- Posiziona i Campioni ---
        # Posiziona le squadre sulla scacchiera
        self.setup_board_positions()
        
        self.is_over = False
        self.winner = None
        self.clock = pygame.time.Clock() # Per calcolare il delta_time

    # In battle.py, sostituisci l'intero metodo create_battle_copies (inizia circa alla riga 30)

    def create_battle_copies(self, base_team):
        """ 
        Crea copie da battaglia dei campioni.
        Questa funzione ORA FORZA i dati corretti presi dal database.
        """
        battle_team = []
        for c in base_team:
            
            # --- IL MARTELLO ---
            # Non ci fidiamo del campione 'c'. Cerchiamo il campione "vero"
            # nel nostro database per recuperare i dati che potrebbero mancare.
            
            # 1. Trova il "template" corretto dal database
            template = None
            for db_champ in self.champions_database:
                if db_champ.name == c.name:
                    template = db_champ
                    break
            
            if not template:
                print(f"!!! ERRORE GRAVE: Impossibile trovare {c.name} nel database !!!")
                continue # Salta questo campione

            # 2. Creiamo una NUOVA istanza Champion usando i dati del template
            #    e sovrascrivendo con i dati di 'c' (come HP, Livello)
            
            battle_copy = Champion(
                c.name,
                # Usa gli HP di 'c' se esistono, altrimenti quelli del template
                getattr(c, 'base_hp', template.base_hp), 
                getattr(c, 'base_attack', template.base_attack),
                # template.image_path, # Sempre dal template
                getattr(c, 'base_defense', template.base_defense),
                template.crit_chance, # Sempre dal template
                template.mana_max,
                template.mana_start,
                template.attack_speed,
                template.attack_range,
                # template.sprite_path, # <-- Preso a forza dal template!
                # template.sprite_offset_y # <-- Preso a forza!
            )

            # 3. Applica i modificatori di livello (se 'c' era Lvl 2+)
            battle_copy.level = getattr(c, 'level', 1)
            if battle_copy.level > 1:
                multiplier = 1.6 if battle_copy.level == 2 else 2.5
                battle_copy.base_hp = int(battle_copy.base_hp * multiplier)
                battle_copy.base_attack = int(battle_copy.base_attack * multiplier)
            
            # 4. Finalizza le statistiche di battaglia
            battle_copy.max_hp = getattr(c, 'max_hp', battle_copy.base_hp) # Usa gli HP max se potenziati
            battle_copy.hp = battle_copy.max_hp # Full vita
            battle_copy.current_mana = battle_copy.mana_start
            
            # 5. Carica lo sprite (ora il percorso è garantito)
            # if battle_copy.sprite_path:
            #     try:
            #         print(f"Caricamento FORZATO: {battle_copy.sprite_path}")
            #         img = pygame.image.load(battle_copy.sprite_path).convert_alpha()
            #         battle_copy.battle_sprite = pygame.transform.scale(img, SPRITE_SIZE)
            #     except Exception as e:
            #         print(f"--- ERRORE --- Impossibile caricare {battle_copy.sprite_path}: {e}")
            #         battle_copy.battle_sprite = None
            # else:
            #     print(f"Attenzione: {battle_copy.name} non ha 'sprite_path' nel database.")
            #     battle_copy.battle_sprite = None
            
            battle_team.append(battle_copy)
        return battle_team

    def setup_board_positions(self):
        """ Assegna le posizioni X, Y iniziali ai campioni """
        # Coordinate fisse per 3 slot (da migliorare in futuro)
        player_positions = [(400, 300), (400, 400), (400, 500)]
        enemy_positions = [(800, 300), (800, 400), (800, 500)]
        
        for i, champ in enumerate(self.player_team):
            if i < len(player_positions):
                champ.x, champ.y = player_positions[i]
                
        for i, champ in enumerate(self.enemy_team):
            if i < len(enemy_positions):
                champ.x, champ.y = enemy_positions[i]

    def handle_event(self, event):
        # Per ora, la battaglia è automatica, non gestiamo input
        pass

    def update(self):
        """ Loop di update della battaglia, chiamato 60 volte al secondo """
        if self.is_over:
            return
            
        # Calcola il tempo passato (in secondi)
        delta_time = self.clock.tick(60) / 1000.0
        if delta_time > 0.1: delta_time = 0.1 # Limite massimo

        # --- CICLO DI GIOCO PRINCIPALE ---
        for champ in self.all_champs:
            
            if not champ.is_alive():
                continue
            
            # 1. LOGICA BERSAGLIO
            if not champ.target or not champ.target.is_alive():
                if champ in self.player_team:
                    champ.find_closest_target(self.enemy_team)
                else:
                    champ.find_closest_target(self.player_team)
            
            # Se non ci sono più bersagli, la battaglia è finita
            if not champ.target:
                continue

            # Aggiorna la direzione in cui il campione sta guardando
            if champ.target.x > champ.x:
                champ.facing_right = True
            else:
                champ.facing_right = False
                
            # Aggiorna il timer dell'abilità
            if champ.spell_animation_timer > 0:
                champ.spell_animation_timer -= delta_time
                if champ.spell_animation_timer <= 0:
                    champ.spell_effect_image = None # Rimuovi l'effetto quando finisce

            # 2. LOGICA AZIONE (Movimento o Attacco)
            distance = champ.get_distance(champ.target)
            
            if distance > champ.attack_range:
                # 2a. MUOVITI (se fuori range)
                champ.move_towards_target(delta_time)
            
            else:
                # 2b. ATTACCA (se in range)
                champ.attack_timer += delta_time
                
                # Calcola il tempo necessario per un attacco
                time_per_attack = 1.0 / champ.attack_speed
                
                if champ.attack_timer >= time_per_attack:
                    champ.attack_timer = 0 # Resetta il timer
                    
                    # 3. LOGICA ABILITÀ
                    if champ.current_mana >= champ.mana_max:
                        # Lancia l'abilità!
                        champ.cast_spell(self.enemy_team, self.player_team)
                    else:
                        # Altrimenti, attacco base
                        champ.basic_attack(champ.target)
                        # if self.attack_sound:
                        #     try: self.attack_sound.play()
                        #     except: pass # Evita crash se l'audio fallisce
        
        # --- CONTROLLO FINE BATTAGLIA ---
        if not any(c.is_alive() for c in self.enemy_team):
            self.is_over = True
            self.winner = "player"
        elif not any(c.is_alive() for c in self.player_team):
            self.is_over = True
            self.winner = "enemy"

    def draw_hp_bar(self, surface, champ):
        """ Disegna la barra HP e Mana sopra la pedina """
        BAR_WIDTH = 40
        BAR_HEIGHT = 5
        
        x = champ.x
        
        # --- MODIFICA CORRETTA ---
        # Prima calcolavamo la Y in base all'altezza dello sprite.
        # Ora abbiamo un cerchio di raggio 25.
        # Ci posizioniamo 40 pixel sopra il centro (25 raggio + 15 spazio).
        y = champ.y - 40 
        
        # HP
        ratio = champ.hp / max(1, champ.max_hp)
        pygame.draw.rect(surface, RED, (x - BAR_WIDTH/2, y, BAR_WIDTH, BAR_HEIGHT))
        pygame.draw.rect(surface, GREEN, (x - BAR_WIDTH/2, y, BAR_WIDTH * ratio, BAR_HEIGHT))
        
        # MANA
        mana_y = y + BAR_HEIGHT + 2
        if champ.mana_max > 0:
            mana_ratio = champ.current_mana / max(1, champ.mana_max)
            pygame.draw.rect(surface, (40, 40, 40), (x - BAR_WIDTH/2, mana_y, BAR_WIDTH, BAR_HEIGHT))
            pygame.draw.rect(surface, BLUE, (x - BAR_WIDTH/2, mana_y, BAR_WIDTH * mana_ratio, BAR_HEIGHT))

    def draw(self, surface):
        """ Disegna l'intera battaglia (SENZA IMMAGINI - Solo forme geometriche) """
        surface.fill((15, 15, 15)) # Sfondo scuro
        
        # Disegna il "campo di battaglia" (rettangolo grigio scuro)
        pygame.draw.rect(surface, (30, 30, 40), (100, 100, 1000, 600))

        # --- DISEGNA I CAMPIONI (CERCHI) ---
        for champ in self.all_champs:
            if champ.is_alive():
                
                cx, cy = int(champ.x), int(champ.y)

                # 1. Disegna il corpo (Cerchio con il colore del campione)
                # Usa il colore definito in champions.py
                pygame.draw.circle(surface, champ.color, (cx, cy), 25)
                
                # 2. Indicatore Squadra (Anello esterno sottile)
                # Verde per Player, Rosso per Nemico (così si distinguono le squadre)
                team_color = (0, 255, 0) if champ in self.player_team else (255, 0, 0)
                pygame.draw.circle(surface, team_color, (cx, cy), 29, width=2)

                # 3. Indicatore Livello (Bordo Oro interno se Lvl 2+)
                if getattr(champ, 'level', 1) >= 2:
                    pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 25, width=3)

                # 4. Iniziale del Nome (al centro del cerchio)
                # (Es. "G" per Garen)
                # Fix per Ezreal: Sfondo giallo richiede testo nero
                text_color = BLACK if champ.name == "Ezreal" else WHITE
                draw_text(champ.name[0], TEXT_FONT, text_color, surface, champ.x, champ.y)

                # 5. EFFETTO ABILITÀ (Geometrico)
                # Se sta castando, disegniamo un "esplosione" (cerchio bianco vuoto attorno)
                if champ.spell_animation_timer > 0:
                    # Un cerchio bianco che pulsa/circonda il campione
                    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 40, width=3)

                # --- Disegna le barre HP/Mana ---
                # (Richiama la tua funzione che disegna i rettangolini)
                self.draw_hp_bar(surface, champ)

                # --- Disegna i popup danno (Testo fluttuante) ---
                for popup in list(champ.damage_popup_texts): 
                    text_obj = TEXT_FONT.render(popup["text"], True, popup["color"])
                    
                    # Fai salire il testo nel tempo
                    popup["pos"][1] -= 0.5 
                    
                    # Disegna il testo
                    popup_rect = text_obj.get_rect(center=(int(popup["pos"][0]), int(popup["pos"][1])))
                    surface.blit(text_obj, popup_rect)
                    
                    # Aggiorna timer
                    popup["timer"] -= self.clock.get_time() / 1000.0
                    if popup["timer"] <= 0:
                        champ.damage_popup_texts.remove(popup)
                        
        # --- Disegna il terreno (opzionale, sopra i campioni per un effetto) ---
        # (Qui potremmo aggiungere erba, rocce, ecc. se vogliamo)
        # pygame.draw.rect(surface, (50, 80, 50), (100, 100, 1000, 600), 5) # Bordo verde