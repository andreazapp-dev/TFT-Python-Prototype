# champions.py
import pygame
import random
import os
import math

# --- DEFINIZIONE COLORI (Greyboxing) ---
# Assegniamo un colore unico a ogni campione per distinguerli
CHAMP_COLORS = {
    "Garen": (0, 0, 200),      # Blu (Tank)
    "Vi": (200, 0, 200),       # Viola (Bruiser)
    "Ahri": (255, 105, 180),   # Rosa (Mago)
    "Ezreal": (255, 255, 0),   # Giallo (ADC)
    "Aurelion": (0, 0, 100),   # Blu Notte (Drago)
    "Riven": (200, 100, 100),  # Rosso chiaro (Combattente)
    "Shen": (100, 0, 200)      # Viola scuro (Tank)
}
DEFAULT_COLOR = (128, 128, 128) # Grigio default

class Champion:
    """
    Classe che rappresenta un campione con statistiche di base e di combattimento.
    """
    def __init__(self, name, hp, attack,
                 defense=0, crit_chance=0.1, 
                 mana_max=100, mana_start=0, attack_speed=0.7, attack_range=1):
        
        # --- Statistiche Base ---
        self.name = name
        # self.image_path = image_path
        # self.sprite_path = sprite_path
        self.level = 1
        self.color = CHAMP_COLORS.get(name, DEFAULT_COLOR)
        
        # Statistiche che scalano
        self.base_hp = int(hp)
        self.base_attack = int(attack)
        self.base_defense = int(defense)
        self.crit_chance = float(crit_chance)
        
        # --- Statistiche Auto-Battler ---
        self.mana_max = int(mana_max)
        self.mana_start = int(mana_start)
        self.attack_speed = float(attack_speed) # Attacchi al secondo
        self.attack_range = int(attack_range) # 1 = melee, >1 = ranged
        
        # --- Stato di Combattimento (variabili) ---
        self.hp = self.base_hp
        self.max_hp = self.base_hp
        self.current_mana = self.mana_start
        
        self.x = 0 # Posizione reale (pixel)
        self.y = 0
        self.target = None # Il nemico che sta bersagliando
        self.attack_timer = 0.0 # Timer per la velocità d'attacco
        self.is_casting = False
        self.move_speed = 100 # Pixel al secondo

        # --- Grafica ---
        # self.image = None # L'immagine della carta (per lo shop)
        # self.battle_sprite = None # L'immagine del campione in battaglia
        # self.sprite_offset_y = sprite_offset_y  # Offset verticale per il rendering del sprite
        # self.facing_right = True # Per il flip orizzontale
        self.damage_popup_texts = [] # Lista di (text, color, pos, timer) per i popup danno
        self.spell_animation_timer = 0 # Timer per le animazioni abilità
        # self.spell_effect_image = None # Immagine per l'effetto dell'abilità
        
    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def get_distance(self, other_champ):
        """ Calcola la distanza (euclidea) da un altro campione """
        return math.sqrt((self.x - other_champ.x)**2 + (self.y - other_champ.y)**2)

    def find_closest_target(self, enemy_team):
        """ Trova il nemico vivo più vicino """
        closest_dist = float('inf')
        closest_enemy = None
        
        for enemy in enemy_team:
            if enemy.is_alive():
                dist = self.get_distance(enemy)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = enemy
        self.target = closest_enemy

    def move_towards_target(self, delta_time):
        """ Fa un passo verso il bersaglio """
        if not self.target:
            return
            
        # Calcola la direzione
        dir_x = self.target.x - self.x
        dir_y = self.target.y - self.y
        dist = math.sqrt(dir_x**2 + dir_y**2)
        
        if dist == 0: return # Già arrivato
            
        # Normalizza e muovi
        dir_x /= dist
        dir_y /= dist
        
        self.x += dir_x * self.move_speed * delta_time
        self.y += dir_y * self.move_speed * delta_time

    def basic_attack(self, target):
        """ Esegue un attacco base """
        if not target or not target.is_alive():
            return
            
        crit = random.random() < self.crit_chance
        damage = self.base_attack * (2 if crit else 1) - target.base_defense
        damage = max(1, int(damage))
        
        target.take_damage(damage)

        # Aggiungi il popup del danno
        text_color = (255, 0, 0) if crit else (255, 255, 0) # Rosso per crit, Giallo per normale
        target.damage_popup_texts.append({
            "text": str(damage),
            "color": text_color,
            "pos": [target.x, target.y - 40], # Sopra la testa
            "timer": 1.0 # Dura 1 secondo
        })
        
        # Guadagna mana
        self.current_mana = min(self.mana_max, self.current_mana + 10)
        
        print(f"{self.name} attacca {target.name} per {damage} danni. (Mana: {self.current_mana})")
        if not target.is_alive():
            print(f"💀 {target.name} è stato sconfitto!\n")
            self.target = None # Cerca un nuovo bersaglio

    def cast_spell(self, enemy_team, friendly_team):
        """ Esegue l'abilità speciale! """
        print(f"✨✨✨ {self.name} USA L'ABILITÀ SPECIAL! ✨✨✨")
        self.is_casting = True
        self.spell_animation_timer = 1.0 # L'animazione dura 1 secondo
        
        # --- QUI VA LA LOGICA DELLE ABILITÀ ---
        if self.name == "Ahri":
            if self.target and self.target.is_alive():
                print(f"Ahri lancia una Sfera Mistica su {self.target.name}!")
                self.target.take_damage(150) # Danno magico
                
                # img = pygame.image.load(os.path.join("images", "ahri_q.png")).convert_alpha()
                # self.spell_effect_image = pygame.transform.scale(img, SPELL_EFFECT_SIZE)

        elif self.name == "Garen":
            print("Garen usa GIUDIZIO!")
            for enemy in enemy_team:
                if enemy.is_alive() and self.get_distance(enemy) < 150: 
                    enemy.take_damage(100)
            
            # img = pygame.image.load(os.path.join("images", "garen_e.png")).convert_alpha()
            # self.spell_effect_image = pygame.transform.scale(img, SPELL_EFFECT_SIZE)
        
        else:
            print(f"{self.name} si cura di 50 HP!")
            self.hp = min(self.max_hp, self.hp + 50)
            
            # img = pygame.image.load(os.path.join("images", "heal_effect.png")).convert_alpha()
            # self.spell_effect_image = pygame.transform.scale(img, SPELL_EFFECT_SIZE)
        
        # Fine abilità
        self.current_mana = 0
        self.is_casting = False # Per ora è istantanea

SPRITE_SIZE = (70, 70)
SPELL_EFFECT_SIZE = (50, 50)

def get_available_champions():
    """
    Restituisce una lista di campioni disponibili con TUTTE le stats.
    Range: 1 = Melee (50px), 3 = Ranged (300px), 5 = Long Ranged (500px)
    """
    # base_path = os.path.join("images")

    # Range in pixel reali
    R_MELEE = 80 
    R_RANGED = 300
    R_SNIPER = 500

    return [
        # Garen
        Champion("Garen", 650, 50, defense=10, crit_chance=0.1, 
                 mana_max=100, mana_start=0, attack_speed=0.6, attack_range=R_MELEE),
        
        # Vi
        Champion("Vi", 600, 60, defense=8, crit_chance=0.1, 
                 mana_max=80, mana_start=0, attack_speed=0.7, attack_range=R_MELEE),
                 
        # Ahri
        Champion("Ahri", 500, 40, defense=5, crit_chance=0.2, 
                 mana_max=70, mana_start=10, attack_speed=0.75, attack_range=R_RANGED),

        # Ezreal
        Champion("Ezreal", 500, 45, defense=4, crit_chance=0.25, 
                 mana_max=60, mana_start=0, attack_speed=0.8, attack_range=R_SNIPER),

        # Aurelion
        Champion("Aurelion", 700, 30, defense=5, crit_chance=0.2, 
                 mana_max=120, mana_start=40, attack_speed=0.65, attack_range=R_RANGED),

        # Riven
        Champion("Riven", 550, 55, defense=8, crit_chance=0.15, 
                 mana_max=100, mana_start=0, attack_speed=0.7, attack_range=R_MELEE),
                 
        # Shen
        Champion("Shen", 700, 45, defense=12, crit_chance=0.1, 
                 mana_max=100, mana_start=50, attack_speed=0.65, attack_range=R_MELEE),
    ]