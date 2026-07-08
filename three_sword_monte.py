import random
import textwrap

STANCE_SYMBOLS = {
    'R': 'Rock',
    'P': 'Paper',
    'S': 'Scissors'
}

BEATS = {
    'R': 'S',
    'P': 'R',
    'S': 'P'
}

UNIT_TEMPLATES = [
    ('Squire', ['R', 'P']),
    ('Knight', ['P', 'S']),
    ('Ranger', ['S', 'R'])
]

ENEMY_NAMES = ['Raider', 'Marauder', 'Fencer']


def wrap(text):
    return textwrap.fill(text, width=70)


class Unit:
    def __init__(self, name, stances):
        self.name = name
        self.stances = stances
        self.hp = 6
        self.max_hp = 6
        self.combo_history = []
        self.barrier_turns = 0
        self.weakness_turns = 0

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def status_line(self):
        alive_status = 'ALIVE' if self.alive else 'DEFEATED'
        return f'{self.name}: {self.hp}/{self.max_hp} HP - {alive_status}'

    def available_stances(self):
        return ' '.join(STANCE_SYMBOLS[s] for s in self.stances)

    def can_use(self, stance):
        return stance in self.stances

    def can_use_attack(self, stance):
        if self.weakness_turns > 0 and stance == 'R':
            return False
        return self.can_use(stance)

    def record_attack(self, attack):
        self.combo_history.append(attack)
        if len(self.combo_history) > 3:
            self.combo_history.pop(0)

    def trigger_combo_effect(self, target, sequence=None):
        if len(self.combo_history) < 3 and sequence is None:
            return None

        if sequence is None:
            sequence = ''.join(self.combo_history[-3:])
        if sequence == 'SRS':
            self.combo_history.clear()
            target.take_damage(3)
            return 'heavy'
        if sequence == 'RRR':
            self.combo_history.clear()
            self.barrier_turns = 3
            return 'barrier'
        if sequence == 'PPS':
            self.combo_history.clear()
            target.weakness_turns = 3
            return 'weakness'
        return None

    def tick_status_effects(self):
        self.barrier_turns = max(0, self.barrier_turns - 1)
        self.weakness_turns = max(0, self.weakness_turns - 1)


class Army:
    def __init__(self, units):
        self.units = units

    def alive_units(self):
        return [unit for unit in self.units if unit.alive]

    def all_defeated(self):
        return all(not unit.alive for unit in self.units)

    def summary(self):
        return '\n'.join(unit.status_line() for unit in self.units)

    def choose_ai_unit(self):
        alive = self.alive_units()
        if not alive:
            return None
        best = sorted(alive, key=lambda u: (u.hp, random.random()))[0]
        return best

    def choose_ai_stances(self, unit):
        if unit.weakness_turns > 0:
            options = [stance for stance in unit.stances if stance != 'R']
            if options:
                return random.choice(options)
        return random.choice(unit.stances)


def get_player_choice(prompt, choices):
    while True:
        choice = input(prompt).strip()
        if choice in choices:
            return choice
        print('Invalid choice. Try again.')


def parse_attacks(raw, unit):
    parts = raw.upper().split()
    if len(parts) != 1:
        return None
    attack = parts[0]
    if attack not in STANCE_SYMBOLS:
        return None
    if not unit.can_use_attack(attack):
        return None
    return attack


def compare_stances(attacker, defender):
    if attacker == defender:
        return 0
    if BEATS[attacker] == defender:
        return 1
    return -1


def print_header():
    print('=' * 76)
    print('3 SWORD MONTE'.center(76))
    print('=' * 76)


def print_intro():
    intro = (
        'You have been challenged to a duel; there is no escape. In the shadow of a medieval ' 
        'battlefield, three units stand ready. Each of your warriors bears two hidden stances, ' 
        'each stance repeated twice across your three units. Each turn, a chosen unit will unleash ' 
        'a single attack. Land a combo sequence to trigger a special move: SRS for a heavy attack, ' 
        'RRR for a barrier, or PPS for a weakness attack. Victory comes to the side that knocks out all three enemy units.'
    )
    print(wrap(intro))
    print()
    print('Stances: R = Rock, P = Paper, S = Scissors')
    print('Damage: Win = 2, Tie = 1 each, Loss = 0')
    print('Each unit has 6 HP.')
    print()


def create_player_army():
    return Army([Unit(name, stances) for name, stances in UNIT_TEMPLATES])


def create_enemy_army():
    stances = ['R', 'R', 'P', 'P', 'S', 'S']
    random.shuffle(stances)
    units = []
    for name in ENEMY_NAMES:
        picks = [stances.pop(), stances.pop()]
        units.append(Unit(name, picks))
    return Army(units)


def choose_player_unit(army):
    alive = army.alive_units()
    while True:
        print('Your army:')
        for idx, unit in enumerate(alive, start=1):
            print(f'  {idx}) {unit.name} - {unit.hp}/6 HP - Stances: {unit.available_stances()}')
        choice = input('Choose your active unit number: ').strip()
        if not choice.isdigit():
            print('Enter a number.')
            continue
        index = int(choice) - 1
        if 0 <= index < len(alive):
            return alive[index]
        print('Invalid unit number.')


def choose_faction():
    choices = {
        'aggressive': 'aggressive',
        'a': 'aggressive',
        'balanced': 'balanced',
        'b': 'balanced',
        'defensive': 'defensive',
        'd': 'defensive'
    }
    while True:
        print('Choose your faction: aggressive, balanced, defensive')
        choice = input('Faction: ').strip().lower()
        if choice in choices:
            return choices[choice]
        print('Invalid faction. Choose aggressive, balanced, or defensive.')


def choose_target_unit(army, label):
    alive = army.alive_units()
    while True:
        print(f'{label}:')
        for idx, unit in enumerate(alive, start=1):
            print(f'  {idx}) {unit.name} - {unit.hp}/6 HP')
        choice = input(f'Choose {label.lower()} number: ').strip()
        if not choice.isdigit():
            print('Enter a number.')
            continue
        index = int(choice) - 1
        if 0 <= index < len(alive):
            return alive[index]
        print('Invalid choice.')


def collect_player_attacks(unit):
    print(f'Your {unit.name} may use: {unit.available_stances()}')
    print('Enter one attack using R, P, or S. Combos: SRS, RRR, PPS.')
    while True:
        raw = input('Attack: ').strip()
        attack = parse_attacks(raw, unit)
        if attack:
            return attack
        print('Invalid attack. Choose one valid stance from this unit.')


def resolve_volley(player_unit, enemy_unit, player_attacks, enemy_attacks, player_faction):
    print('=' * 76)
    print(f'{player_unit.name} vs {enemy_unit.name} - round begins')
    print('-' * 76)

    player_name = STANCE_SYMBOLS[player_attacks]
    enemy_name = STANCE_SYMBOLS[enemy_attacks]
    print(f'{player_unit.name} used {player_name}, {enemy_unit.name} used {enemy_name}.')
    print(f'{player_unit.name} fights with a {player_faction} faction.')

    combo = player_unit.trigger_combo_effect(enemy_unit)
    if combo == 'heavy':
        print(f'  {player_unit.name} triggers a heavy attack!')
        enemy_unit.take_damage(3)
    elif combo == 'barrier':
        print(f'  {player_unit.name} raises a defensive barrier!')
    elif combo == 'weakness':
        print(f'  {player_unit.name} inflicts weakness on {enemy_unit.name}!')
    else:
        result = compare_stances(player_attacks, enemy_attacks)
        if result == 1:
            enemy_damage = 2
            if player_faction == 'aggressive':
                enemy_damage += 1
                print(f'  Aggressive faction adds 1 damage to the winning attack!')
            enemy_unit.take_damage(enemy_damage)
            print(f'  {enemy_unit.name} takes {enemy_damage} damage.')
        elif result == -1:
            damage = 2
            if player_unit.barrier_turns > 0:
                damage = max(0, damage - 1)
                print(f'  {player_unit.name} blocks 1 damage with its barrier!')
            player_unit.take_damage(damage)
            print(f'  {player_unit.name} takes {damage} damage.')
            if player_faction == 'defensive':
                enemy_unit.take_damage(1)
                print(f'  Defensive faction deals 1 damage on the loss!')
        else:
            player_damage = 1
            enemy_damage = 1
            if player_unit.barrier_turns > 0:
                player_damage = max(0, player_damage - 1)
                print(f'  {player_unit.name} blocks 1 damage with its barrier!')
            if player_faction == 'balanced':
                enemy_damage += 1
                print(f'  Balanced faction adds 1 damage to the tie!')
            player_unit.take_damage(player_damage)
            enemy_unit.take_damage(enemy_damage)
            print(f'  {player_unit.name} takes {player_damage} damage, {enemy_unit.name} takes {enemy_damage} damage.')

    if player_unit.barrier_turns > 0:
        print(f'  {player_unit.name} is protected by its barrier this round.')

    print('-' * 76)
    print(f'Current status: {player_unit.name} {player_unit.hp}/6 HP, {enemy_unit.name} {enemy_unit.hp}/6 HP')
    print('-' * 76)

    print('=' * 76)
    if not player_unit.alive:
        print(f'{player_unit.name} has been knocked out!')
    if not enemy_unit.alive:
        print(f'{enemy_unit.name} has been knocked out!')
    if player_unit.alive and enemy_unit.alive:
        print('The round ends with both units still standing.')
    print()


def pause_for_enter(message):
    print(message)
    input('Press Enter to continue...')


def game_loop():
    print_header()
    print_intro()
    player_army = create_player_army()
    enemy_army = create_enemy_army()

    turn = 1
    player_unit = None
    player_faction = None
    while True:
        print(f'--- Turn {turn} ---')
        print('Your army status:')
        print(player_army.summary())
        print()
        print('Enemy army status:')
        print(enemy_army.summary())
        print()

        if player_army.all_defeated():
            pause_for_enter('Game over, you lose!')
            break
        if enemy_army.all_defeated():
            pause_for_enter('Game over, you win!')
            break

        if player_unit is None or not player_unit.alive:
            player_unit = choose_player_unit(player_army)
            player_faction = choose_faction()
        else:
            print(f'{player_unit.name} remains your active unit with a {player_faction} faction.')

        enemy_unit = enemy_army.choose_ai_unit()
        if enemy_unit is None:
            print('No enemy unit to fight.')
            break

        player_attacks = collect_player_attacks(player_unit)
        player_unit.record_attack(player_attacks)
        enemy_attacks = enemy_army.choose_ai_stances(enemy_unit)

        print(f'Enemy {enemy_unit.name} prepares its attacks.')
        resolve_volley(player_unit, enemy_unit, player_attacks, enemy_attacks, player_faction)

        player_unit.tick_status_effects()
        enemy_unit.tick_status_effects()

        turn += 1

    print('Game over.')


if __name__ == '__main__':
    random.seed()
    game_loop()
