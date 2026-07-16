import random
import textwrap

STANCE_SYMBOLS = {
    'S': 'Strong',
    'P': 'Speed',
    'N': 'Sneaky'
}

ATTACK_POOL = {
    'S': [
        {'name': 'Heavy smash', 'damage': 25, 'recoil': 5},
        {'name': 'Slam', 'damage': 20},
        {'name': 'Tackle', 'damage': 15, 'enemy_damage_reduction': 5},
    ],
    'P': [
        {'name': 'slice', 'damage': 20},
        {'name': 'dodge and repost', 'damage': 15, 'self_shield': 5},
        {'name': 'building speed', 'damage': 15, 'speed_bonus_next_turn': 10},
    ],
    'N': [
        {'name': 'bait', 'damage': 20},
        {'name': 'feint', 'damage': 15, 'heal': 10},
        {'name': 'backstab', 'damage': 30, 'no_tie_damage': True},
    ]
}

BEATS = {
    'S': 'N',
    'P': 'S',
    'N': 'P'
}

UNIT_TEMPLATES = [
    ('Squire', ['S', 'P']),
    ('Knight', ['P', 'N']),
    ('Ranger', ['N', 'S'])
]

ENEMY_NAMES = ['Raider', 'Marauder', 'Fencer']


def wrap(text):
    return textwrap.fill(text, width=70)


class Unit:
    def __init__(self, name, stances):
        self.name = name
        self.stances = stances
        self.hp = 100
        self.max_hp = 100
        self.combo_history = []
        self.weakness_turns = 0
        self.damage_shield = 0
        self.damage_reduction = 0
        self.speed_bonus_next_turn = 0

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def status_line(self):
        alive_status = 'ALIVE' if self.alive else 'DEFEATED'
        return f'{self.name}: {self.hp}/{self.max_hp} HP - {alive_status}'

    def available_stances(self):
        return ' '.join(STANCE_SYMBOLS[s] for s in self.stances)

    def can_use(self, stance):
        return stance in self.stances

    def can_use_attack(self, stance):
        if self.weakness_turns > 0 and stance == 'N':
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
        if sequence == 'NSN':
            self.combo_history.clear()
            target.take_damage(30)
            return 'heavy'
        if sequence == 'SSS':
            self.combo_history.clear()
            self.damage_shield = 10
            return 'barrier'
        if sequence == 'PPN':
            self.combo_history.clear()
            target.weakness_turns = 3
            return 'weakness'
        return None

    def tick_status_effects(self):
        self.weakness_turns = max(0, self.weakness_turns - 1)
        self.damage_shield = 0
        self.damage_reduction = 0

    def get_attack_bonus(self, stance):
        if stance == 'P' and self.speed_bonus_next_turn > 0:
            bonus = self.speed_bonus_next_turn
            self.speed_bonus_next_turn = 0
            return bonus
        return 0


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
            options = [stance for stance in unit.stances if stance != 'N']
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


def format_hp(value):
    if float(value).is_integer():
        return str(int(value))
    return f'{value:.1f}'


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
        'a single stance-based attack from a random move pool. Victory comes to the side that knocks out all three enemy units.'
    )
    print(wrap(intro))
    print()
    print('Stances: S = Strong, N = Sneak, P = Speed')
    print('Damage: Win = full damage, Tie = half damage to both, Loss = 0')
    print('Each unit has 100 HP.')
    print()


def create_player_army():
    return Army([Unit(name, stances) for name, stances in UNIT_TEMPLATES])


def create_enemy_army():
    stances = ['S', 'S', 'P', 'P', 'N', 'N']
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
            print(f'  {idx}) {unit.name} - {unit.hp}/100 HP - Stances: {unit.available_stances()}')
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
        print('Choose your faction: Aggressive, Balanced, Defensive')
        choice = input('Faction: ').strip().lower()
        if choice in choices:
            return choices[choice]
        print('Invalid faction. Choose Aggressive, Balanced, or Defensive.')


def choose_target_unit(army, label):
    alive = army.alive_units()
    while True:
        print(f'{label}:')
        for idx, unit in enumerate(alive, start=1):
            print(f'  {idx}) {unit.name} - {unit.hp}/100 HP')
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
    print('Enter one stance using S, P, or N. A random move from that category will be used.')
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
    player_move = random.choice(ATTACK_POOL[player_attacks])
    enemy_move = random.choice(ATTACK_POOL[enemy_attacks])
    print(f'{player_unit.name} used {player_name}: {player_move["name"]}.')
    print(f'{enemy_unit.name} used {enemy_name}: {enemy_move["name"]}.')
    print(f'{player_unit.name} fights with a {player_faction} faction.')

    result = compare_stances(player_attacks, enemy_attacks)
    player_damage = player_move['damage']
    enemy_damage = enemy_move['damage']

    if player_attacks == 'P':
        player_damage += player_unit.get_attack_bonus(player_attacks)
    if enemy_attacks == 'P':
        enemy_damage += enemy_unit.get_attack_bonus(enemy_attacks)

    if player_move.get('speed_bonus_next_turn'):
        player_unit.speed_bonus_next_turn = max(player_unit.speed_bonus_next_turn, player_move['speed_bonus_next_turn'])
        print(f'  {player_unit.name} gains +{player_move["speed_bonus_next_turn"]} damage to speed attacks next turn.')
    if enemy_move.get('speed_bonus_next_turn'):
        enemy_unit.speed_bonus_next_turn = max(enemy_unit.speed_bonus_next_turn, enemy_move['speed_bonus_next_turn'])

    if player_move.get('enemy_damage_reduction'):
        enemy_unit.damage_reduction = max(enemy_unit.damage_reduction, player_move['enemy_damage_reduction'])
        print(f'  {enemy_unit.name} will deal {player_move["enemy_damage_reduction"]} less damage this turn!')
    if enemy_move.get('enemy_damage_reduction'):
        player_unit.damage_reduction = max(player_unit.damage_reduction, enemy_move['enemy_damage_reduction'])

    if player_move.get('self_shield'):
        player_unit.damage_shield = max(player_unit.damage_shield, player_move['self_shield'])
        print(f'  {player_unit.name} avoids {player_move["self_shield"]} damage this round.')
    if enemy_move.get('self_shield'):
        enemy_unit.damage_shield = max(enemy_unit.damage_shield, enemy_move['self_shield'])

    if player_move.get('recoil'):
        player_unit.take_damage(player_move['recoil'])
        print(f'  {player_unit.name} takes {player_move["recoil"]} recoil damage.')
    if enemy_move.get('recoil'):
        enemy_unit.take_damage(enemy_move['recoil'])

    if player_move.get('heal'):
        player_unit.heal(player_move['heal'])
        print(f'  {player_unit.name} heals {player_move["heal"]} HP.')
    if enemy_move.get('heal'):
        enemy_unit.heal(enemy_move['heal'])

    if result == 1:
        if player_faction == 'aggressive':
            player_damage += 10
            print('  Aggressive faction adds 10 damage to the winning attack!')
        if player_move.get('name') == 'backstab':
            print('  Backstab strikes true!')
        player_damage = max(0, player_damage)
        enemy_damage = 0
        enemy_taken = max(0, player_damage - enemy_unit.damage_shield - enemy_unit.damage_reduction)
        enemy_unit.take_damage(enemy_taken)
        print(f'  {enemy_unit.name} takes {enemy_taken} damage.')
    elif result == -1:
        if player_faction == 'defensive' and player_move['name'] == 'Tackle':
            enemy_unit.take_damage(10)
            print('  Defensive faction deals 10 damage on the loss!')
        print(f'  {player_unit.name} deals no damage.')
        player_damage = 0
    else:
        if player_move.get('no_tie_damage'):
            player_damage = 0
            print('  Backstab does no damage on a tie.')
        player_damage *= 0.5
        enemy_damage *= 0.5
        player_taken = max(0, player_damage - player_unit.damage_shield - player_unit.damage_reduction)
        enemy_taken = max(0, enemy_damage - enemy_unit.damage_shield - enemy_unit.damage_reduction)
        player_unit.take_damage(player_taken)
        enemy_unit.take_damage(enemy_taken)
        print(f'  {player_unit.name} takes {player_taken} damage, {enemy_unit.name} takes {enemy_taken} damage.')

    if result == 1:
        player_taken = max(0, enemy_damage - player_unit.damage_shield - player_unit.damage_reduction)
        player_unit.take_damage(player_taken)
        if player_taken > 0:
            print(f'  {player_unit.name} takes {player_taken} damage.')
    elif result == -1:
        enemy_taken = max(0, player_damage - enemy_unit.damage_shield - enemy_unit.damage_reduction)
        if enemy_taken > 0:
            enemy_unit.take_damage(enemy_taken)
            print(f'  {enemy_unit.name} takes {enemy_taken} damage.')

    player_unit.damage_shield = 0
    enemy_unit.damage_shield = 0
    player_unit.damage_reduction = 0
    enemy_unit.damage_reduction = 0

    print('-' * 76)
    print(f'Current status: {player_unit.name} {format_hp(player_unit.hp)}/100 HP, {enemy_unit.name} {format_hp(enemy_unit.hp)}/100 HP')
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
