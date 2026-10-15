import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/game_data.db')
cur = conn.cursor()

names = ['Baphomet', 'Phreeoni', 'Pharaoh', 'Goblin Leader', 'Drake', 'Maya', 'Golden Thief Bug', 'Moonlight Flower', 'Eddga', 'Mistress', 'Orc Hero', 'Orc Lord', 'Doppelganger', 'Osiris', 'Dark Lord', 'Dracula']

cur.execute('SELECT id, name, type, type_name, is_mvp, is_mini, is_canonical, card_id FROM monsters WHERE id IN (30018, 30021)')
print('Monsters 30018, 30021:', cur.fetchall())

cur.execute('SELECT id, name, is_mvp, monster_id FROM cards WHERE name LIKE "%Baphomet%"')
print('Baphomet cards:', cur.fetchall())

# Let's check how search_monsters(category="mvp") works in database.py
# In database.py: conditions.append("(is_mvp = 1 OR is_mini = 1)")
# And in search_monsters: canonical_only is None and category != "mvp" -> does NOT filter is_canonical = 1!
# Which means search_monsters(category="mvp") returns monsters with (is_mvp = 1 OR is_mini = 1).
# How many monsters match (is_mvp = 1 OR is_mini = 1)?
cur.execute('SELECT id, name, level, is_mvp, is_mini, is_canonical FROM monsters WHERE is_mvp = 1 OR is_mini = 1')
mvp_tab_monsters = cur.fetchall()
print(f"\nTotal monsters returned in MVP tab: {len(mvp_tab_monsters)}")

# How many of these have linked cards in monster_cards?
with_cards = 0
without_cards = []
for m in mvp_tab_monsters:
    cur.execute('SELECT count(*) FROM monster_cards WHERE monster_id = ?', (m[0],))
    cnt = cur.fetchone()[0]
    if cnt > 0:
        with_cards += 1
    else:
        without_cards.append(m)

print(f"Monsters in MVP tab WITH cards: {with_cards}/{len(mvp_tab_monsters)}")
print(f"Monsters in MVP tab WITHOUT cards: {len(without_cards)}/{len(mvp_tab_monsters)}")

# Group without_cards by unique name
no_card_names = set(m[1] for m in without_cards)
print(f"Unique MVP/Mini names with NO CARDS in MVP tab: {len(no_card_names)}")
print("List of unique MVP/Mini names lacking cards:")
for n in sorted(no_card_names):
    # Check if ANY card in `cards` table matches this name
    cur.execute('SELECT id, name FROM cards WHERE name LIKE ?', (f'%{n}%',))
    matching_cards = cur.fetchall()
    print(f"  - '{n}': {len(matching_cards)} potential cards in DB ({[c[1] for c in matching_cards[:3]]})")

