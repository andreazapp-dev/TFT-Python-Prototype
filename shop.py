# shop.py
import pygame
import random
from champions import Champion, get_available_champions

# Importo da config.py
from config import (
    draw_text, TEXT_FONT, BUTTON_FONT, TITLE_FONT, 
    BLUE, LIGHT_BLUE, GRAY, GOLD, BLACK, GREEN, WHITE, RED, WIDTH, HEIGHT
)

class ShopManager:
    """
    Gestisce la logica e il rendering dello shop.
    È controllato da game.py
    """
    def __init__(self, game, champions_database):
        self.game = game  # Riferimento alla classe Game principale
        self.shop_size = 5
        self.card_size = (150, 150)
        self.spacing_x = 200
        self.margin_y = 180
        
        self.champions_pool = champions_database
        self.shop_champs = [] # I 5 campioni in vendita
        
        # Riferimenti ai bottoni per i click
        # Usiamo 'game.screen' per ottenere WIDTH e HEIGHT
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()
        self.refresh_button_rect = pygame.Rect(screen_width//2 - 200, screen_height - 90, 180, 60)
        self.confirm_button_rect = pygame.Rect(screen_width//2 + 20, screen_height - 90, 180, 60)
        self.buy_buttons = []

        # --- Aggiunte per Drag & Drop ---
        self.is_dragging = False
        self.dragged_champ = None
        self.dragged_from_list = None # 'board' o 'bench'
        self.dragged_from_index = -1
        self.scroll_y = 0

        self.roll_shop(is_free=True)

    def reset(self):
        self.roll_shop(is_free=True)

    def roll_shop(self, is_free=False):
        if not is_free:
            if self.game.player_gold >= 2:
                self.game.player_gold -= 2
            else:
                print("Oro non sufficiente per il Reroll!")
                return
                
        self.shop_champs = [random.choice(self.champions_pool) for _ in range(self.shop_size)]
        
        # for champ in self.shop_champs:
            # Carichiamo le immagini
            # if champ and champ.image_path:
            #     try:
            #         img = pygame.image.load(champ.image_path).convert_alpha()
            #         champ.image = pygame.transform.scale(img, self.card_size)
            #     except Exception as e:
            #         print(f"Errore img shop: {e}")
            #         champ.image = None
        print("Shop ricaricato.")

    # --- Acquisto Campione ---
    def buy_champion(self, champ_to_buy, shop_slot_index):
        # Controlla se la panchina è piena
        if len(self.game.bench) >= self.game.bench_slots:
            print("Panchina piena!")
            return # Non comprare se non c'è spazio

        if self.game.player_gold >= 3:
            self.game.player_gold -= 3
            
            bought_champ = self.shop_champs[shop_slot_index]
            self.shop_champs[shop_slot_index] = None # Slot vuoto
            
            # Aggiungi il campione alla panchina
            self.game.bench.append(bought_champ)
            print(f"Comprato: {bought_champ.name}. Aggiunto alla panchina.")
            
            # Controlla i merge dopo ogni acquisto
            self.merge_champions(bought_champ)
        else:
            print("Oro non sufficiente!")

    # --- Controllo Merge ---
    def merge_champions(self, champ_just_added):
        """
        Controlla i merge per il campione appena aggiunto.
        Scansiona sia board che bench.
        """
        if not champ_just_added:
            return False

        name_to_check = champ_just_added.name
        level_to_check = getattr(champ_just_added, 'level', 1)
        
        # 1. Trova tutte le copie (in entrambe le liste)
        copies_in_board = [c for c in self.game.board if c and c.name == name_to_check and getattr(c, 'level', 1) == level_to_check]
        copies_in_bench = [c for c in self.game.bench if c and c.name == name_to_check and getattr(c, 'level', 1) == level_to_check]
        all_copies = copies_in_board + copies_in_bench
        
        if len(all_copies) < 3:
            return False # Non c'è un merge

        print(f"MERGE DI {name_to_check} Lvl {level_to_check}!")
        base_champ = all_copies[0]
        
        # 2. Rimuovi le 3 copie (da qualsiasi lista provengano)
        count = 0
        for champ_to_remove in all_copies[:3]:
            if champ_to_remove in self.game.board:
                self.game.board.remove(champ_to_remove)
            elif champ_to_remove in self.game.bench:
                self.game.bench.remove(champ_to_remove)
            count += 1
            
        # 3. Crea il campione potenziato
        new_level = level_to_check + 1
        multiplier = 1.6 if new_level == 2 else 2.5 # Lvl 2 o Lvl 3+
        
        upgraded = Champion(
            base_champ.name, 
            int(base_champ.hp * multiplier), 
            int(base_champ.base_attack * multiplier), 
            # base_champ.image_path,
            int(getattr(base_champ, 'defense', 0) * multiplier),
            getattr(base_champ, 'crit_chance', 0.1),
            getattr(base_champ, 'mana_max', 100),
            getattr(base_champ, 'mana_start', 0),
            getattr(base_champ, 'attack_speed', 0.7),
            getattr(base_champ, 'attack_range', 1),
            # getattr(base_champ, 'sprite_path', None), 
            # getattr(base_champ, 'sprite_offset_y', 0)
        )
        upgraded.level = new_level
        upgraded.max_hp = upgraded.hp
        
       #  if upgraded.image_path:
           # try:
             #   img = pygame.image.load(upgraded.image_path).convert_alpha()
              #  upgraded.image = pygame.transform.scale(img, self.card_size)
           # except Exception as e:
           #     upgraded.image = None
        
        # 4. Aggiungi il campione potenziato alla panchina (se c'è spazio)
        if len(self.game.bench) < self.game.bench_slots:
            self.game.bench.append(upgraded)
            print(f"Creato {upgraded.name} Lvl {upgraded.level} e messo in panchina.")
            # Controlla ricorsivamente se questo nuovo campione crea un altro merge!
            self.merge_champions(upgraded)
        else:
            print(f"Creato {upgraded.name} Lvl {upgraded.level}, ma panchina piena! Campione perso.")
            # In un vero TFT, il campione verrebbe "spostato". Per ora, è perso.
            
        return True

    # Sostituisci l'intero metodo handle_event
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        # --- AGGIUNGI QUESTO BLOCCO PER LO SCROLL ---
        if event.type == pygame.MOUSEWHEEL:
            # event.y è 1 se si scorre in su, -1 se si scorre in giù
            # Moltiplichiamo per una velocità (es. 30 pixel)
            self.scroll_y += event.y * 30
            
            # Limitiamo lo scorrimento per non "uscire" dallo schermo
            # 0 è il punto più alto (non si può scorrere più in su)
            # -250 è il punto più basso (limite da aggiustare se serve)
            self.scroll_y = max(-250, min(0, self.scroll_y)) 
            return # Evento gestito
        
        # --- LOGICA DRAG & DROP (Inizio) ---
        if self.is_dragging and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # --- RILASCIO (DROP) ---
            self.is_dragging = False
            
            # Troviamo lo slot più vicino
            board_rects = self.get_board_rects()
            bench_rects = self.get_bench_rects()
            
            # 1. Prova a droppare sulla SCACCHIERA
            for i, rect in enumerate(board_rects):
                if rect.collidepoint(mouse_pos):
                    # Hai droppato su uno slot della scacchiera
                    if len(self.game.board) < self.game.board_slots or i < len(self.game.board):
                        # Metti il campione nello slot (o scambia)
                        self.place_champ_in_list(self.game.board, i, self.game.board_slots)
                        return # Lavoro finito
                    else:
                        break # La scacchiera è piena, non puoi droppare qui
            
            # 2. Prova a droppare sulla PANCHINA
            for i, rect in enumerate(bench_rects):
                if rect.collidepoint(mouse_pos):
                    # Hai droppato su uno slot della panchina
                    self.place_champ_in_list(self.game.bench, i, self.game.bench_slots)
                    return # Lavoro finito

            # 3. Droppato fuori: rimetti il campione da dove è venuto
            self.return_dragged_champ()
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # --- LOGICA VENDITA (Click Destro) ---
            if event.button == 3: # Click destro
                board_rects = self.get_board_rects()
                bench_rects = self.get_bench_rects()
                
                # Controlla scacchiera
                for i, rect in enumerate(board_rects):
                    if rect.collidepoint(mouse_pos) and i < len(self.game.board) and self.game.board[i]:
                        champ_to_sell = self.game.board.pop(i)
                        self.sell_champion(champ_to_sell)
                        return # Venduto
                # Controlla panchina
                for i, rect in enumerate(bench_rects):
                    if rect.collidepoint(mouse_pos) and i < len(self.game.bench) and self.game.bench[i]:
                        champ_to_sell = self.game.bench.pop(i)
                        self.sell_champion(champ_to_sell)
                        return # Venduto
                return # Click destro a vuoto

            # --- LOGICA CLICK SINISTRO ---
            if event.button == 1:
                # 1. Controlla i bottoni UI (Compra, Reroll, Conferma)
                if self.refresh_button_rect.collidepoint(mouse_pos):
                    print("Click Reroll")
                    self.roll_shop()
                    return
                if self.confirm_button_rect.collidepoint(mouse_pos) and len(self.game.board) > 0: # Ora basta > 0
                    print("Click Conferma -> Avvio Battaglia")
                    self.game.start_battle()
                    return
                for i, rect in enumerate(self.buy_buttons):
                    if rect.collidepoint(mouse_pos):
                        champ_in_slot = self.shop_champs[i]
                        if champ_in_slot:
                            print(f"Click Compra slot {i}: {champ_in_slot.name}")
                            self.buy_champion(champ_in_slot, i)
                            return
                
                # 2. Controlla se iniziamo un DRAG
                board_rects = self.get_board_rects()
                bench_rects = self.get_bench_rects()
                
                # Scacchiera
                for i, rect in enumerate(board_rects):
                    if rect.collidepoint(mouse_pos) and i < len(self.game.board) and self.game.board[i]:
                        self.start_dragging(self.game.board, i)
                        return
                # Panchina
                for i, rect in enumerate(bench_rects):
                    if rect.collidepoint(mouse_pos) and i < len(self.game.bench) and self.game.bench[i]:
                        self.start_dragging(self.game.bench, i)
                        return
    
    # Aggiungi questi metodi alla classe ShopManager

    def sell_champion(self, champion):
        """ Logica di vendita """
        # Per ora prezzo fisso, in futuro dipenderà dal costo/livello
        sell_price = 2
        self.game.player_gold += sell_price
        print(f"Venduto {champion.name} per {sell_price}g. Oro totale: {self.game.player_gold}")

    def start_dragging(self, from_list, index):
        """ Prepara un campione per il trascinamento """
        if self.is_dragging: return # Stai già trascinando
        
        self.dragged_champ = from_list.pop(index) # Rimuovi e tieni in mano
        self.dragged_from_list = from_list # Salva da dove è venuto (la lista stessa)
        self.dragged_from_index = index # Salva lo slot originale
        self.is_dragging = True
        print(f"Dragging {self.dragged_champ.name}")

    def place_champ_in_list(self, target_list, target_index, max_slots):
        """ Piazza il campione trascinato in uno slot (o scambia) """
        
        # Assicura che le liste non siano più grandi del loro max
        while len(self.game.board) > self.game.board_slots: self.game.board.pop()
        while len(self.game.bench) > self.game.bench_slots: self.game.bench.pop()
        
        # Controlla se lo slot di destinazione è vuoto
        if target_index >= len(target_list):
            target_list.append(self.dragged_champ)
            # Rimuovi placeholder se necessario (dopo uno swap)
            if self.dragged_from_list == target_list and self.dragged_from_index < len(target_list):
                 target_list.pop(self.dragged_from_index)
        else:
            # Lo slot è occupato: SCAMBIA
            champ_in_slot = target_list[target_index]
            target_list[target_index] = self.dragged_champ
            # Rimetti il campione scambiato da dove sei venuto
            self.dragged_from_list.insert(self.dragged_from_index, champ_in_slot)
            
        self.is_dragging = False
        self.dragged_champ = None

    def return_dragged_champ(self):
        """ Rimette il campione nello slot originale se il drop è invalido """
        if self.dragged_champ:
            self.dragged_from_list.insert(self.dragged_from_index, self.dragged_champ)
        self.is_dragging = False
        self.dragged_champ = None

    def get_board_rects(self):
        """ Calcola i rect della scacchiera per i click """
        rects = []
        x_start = (self.game.screen.get_width() - (self.game.board_slots * 180)) // 2 + 50
        y = self.game.screen.get_height() - 300 + self.scroll_y
        for i in range(self.game.board_slots):
            x = x_start + i * 180
            rects.append(pygame.Rect(x, y, 150, 150))
        return rects
        
    def get_bench_rects(self):
        """ Calcola i rect della panchina per i click """
        rects = []
        x_start = (self.game.screen.get_width() - (self.game.bench_slots * 160)) // 2 + 30
        y = self.game.screen.get_height() - 70 + self.scroll_y
        for i in range(self.game.bench_slots):
            x = x_start + i * 160
            rects.append(pygame.Rect(x, y, 150, 150))
        return rects

    # Sostituisci l'intero metodo draw con questo CORRETTO
    def draw(self, surface):
        surface.fill((20, 20, 20))
        mouse_pos = pygame.mouse.get_pos()
        
        # --- UI ALTA (FISSA) ---
        draw_text("Negozio Campioni", TITLE_FONT, BLUE, surface, surface.get_width() // 2, 60)
        draw_text(f"Oro: {self.game.player_gold}", BUTTON_FONT, GOLD, surface, surface.get_width() - 100, 40)
        draw_text(f"HP: {self.game.player_hp}", BUTTON_FONT, GREEN, surface, 100, 40)
        draw_text(f"Round: {self.game.round_number}", BUTTON_FONT, WHITE, surface, 100, 80)

        # --- DISEGNA NEGOZIO ---
        self.buy_buttons.clear() 
        for i, champ in enumerate(self.shop_champs):
            x = 80 + i * self.spacing_x
            y = self.margin_y + self.scroll_y
            card_rect = pygame.Rect(x, y, *self.card_size)
            if champ: 
                # Greyboxing: Rettangolo colorato
                pygame.draw.rect(surface, champ.color, card_rect, border_radius=10)
                pygame.draw.rect(surface, WHITE, card_rect, width=2, border_radius=10)
                # Fix per Ezreal: Sfondo giallo richiede testo nero
                text_color = BLACK if champ.name == "Ezreal" else WHITE
                draw_text(champ.name, TEXT_FONT, text_color, surface, x + 75, y + 75)
                
                # Bottone Compra
                buy_button = pygame.Rect(x, y + self.card_size[1] + 40, self.card_size[0], 40)
                self.buy_buttons.append(buy_button) 
                can_buy = self.game.player_gold >= 3 and len(self.game.bench) < self.game.bench_slots
                btn_color = GREEN if can_buy else GRAY
                pygame.draw.rect(surface, btn_color, buy_button, border_radius=8)
                draw_text("Compra (3g)", TEXT_FONT, BLACK, surface, buy_button.centerx, buy_button.centery)
            else:
                pygame.draw.rect(surface, (30,30,30), card_rect, border_radius=10)
                self.buy_buttons.append(pygame.Rect(0,0,0,0)) 

        # --- DISEGNA SCACCHIERA ---
        draw_text(f"Scacchiera ({len(self.game.board)}/{self.game.board_slots})", BUTTON_FONT, GOLD, surface, surface.get_width() // 2, HEIGHT - 330 + self.scroll_y)
        board_rects = self.get_board_rects() 
        for i in range(self.game.board_slots):
            rect = board_rects[i]
            pygame.draw.rect(surface, (40, 40, 40), rect, border_radius=10, width=3)
            
            if i < len(self.game.board) and self.game.board[i]:
                champ = self.game.board[i]
                # Greyboxing: Rettangolo colorato nello slot
                # Creiamo un rettangolo leggermente più piccolo dello slot
                champ_rect = rect.inflate(-10, -10) 
                pygame.draw.rect(surface, champ.color, champ_rect, border_radius=10)
                
                name_color = GOLD if getattr(champ, "level", 1) > 1 else WHITE
                draw_text(champ.name, TEXT_FONT, name_color, surface, rect.centerx, rect.bottom + 20)
                # Stelle
                stars = getattr(champ, "level", 1)
                if stars > 1:
                    for s in range(min(stars, 3)):
                        cx = rect.left + 20 + s * 20
                        cy = rect.top - 12
                        pygame.draw.circle(surface, GOLD, (cx, cy), 6)

        # --- DISEGNA PANCHINA ---
        draw_text(f"Panchina ({len(self.game.bench)}/{self.game.bench_slots})", BUTTON_FONT, GOLD, surface, surface.get_width() // 2, HEIGHT - 100 + self.scroll_y)
        bench_rects = self.get_bench_rects()
        for i in range(self.game.bench_slots):
            rect = bench_rects[i]
            pygame.draw.rect(surface, (40, 40, 40), rect, border_radius=10, width=3)
            
            if i < len(self.game.bench) and self.game.bench[i]:
                champ = self.game.bench[i]
                # Greyboxing: Rettangolo colorato
                champ_rect = rect.inflate(-10, -10)
                pygame.draw.rect(surface, champ.color, champ_rect, border_radius=10)
                
                name_color = GOLD if getattr(champ, "level", 1) > 1 else WHITE
                draw_text(champ.name, TEXT_FONT, name_color, surface, rect.centerx, rect.bottom + 20)
                stars = getattr(champ, "level", 1)
                if stars > 1:
                    for s in range(min(stars, 3)):
                        cx = rect.left + 20 + s * 20
                        cy = rect.top - 12
                        pygame.draw.circle(surface, GOLD, (cx, cy), 6)

        # --- UI BASSA (FISSA) ---
        pygame.draw.rect(surface, LIGHT_BLUE, self.refresh_button_rect, border_radius=10)
        draw_text("Reroll (-2g)", BUTTON_FONT, WHITE, surface, self.refresh_button_rect.centerx, self.refresh_button_rect.centery)
        can_confirm = len(self.game.board) > 0 
        btn_color = BLUE if can_confirm else GRAY
        pygame.draw.rect(surface, btn_color, self.confirm_button_rect, border_radius=10)
        draw_text("CONFERMA", BUTTON_FONT, WHITE, surface, self.confirm_button_rect.centerx, self.confirm_button_rect.centery)

        # --- DISEGNA CAMPIONE TRASCINATO (SOPRA TUTTO) ---
        # CORREZIONE IMPORTANTE: Usiamo il colore, non l'immagine!
        if self.is_dragging and self.dragged_champ:
            # Disegniamo un cerchio sotto il mouse mentre trasciniamo
            pygame.draw.circle(surface, self.dragged_champ.color, mouse_pos, 40)
            pygame.draw.circle(surface, WHITE, mouse_pos, 40, width=2)