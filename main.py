#!/usr/bin/env python
import time

# import the json library to read from JSON files
import json

#import the copy module
from copy import deepcopy

# import the MUD server class
from mudserver import MudServer

with open('config.json') as f:
    data = json.load(f)

# structure defining the rooms in the game. Try adding more rooms to the game!
rooms =  data["areas"]
"""{
    "Riven": {
        "description": "You are in the city of Riven, a simple town with a blacksmith and a tavern. The tavern is well known for it's cooking. There is a sign that says \"Area is a WIP\". ",
        "exits": {"tavern": "Tavern", "blacksmith": "Blacksmith"},
    },
    "Tavern": {
        "description": "You're in the Boar's Tooth Tavern. There are several tables and a bar. There is a sign that says \"Area is a WIP\". ",
        "exits": {"outside": "Riven"},
    },
    "Blacksmith": {
        "description": "You're in the Riven Blacksmith. Swords line the walls. There is a sign that says \"Area is a WIP\". ",
        "exits": {"outside": "Riven"}
    }
}"""

money_conversion = data["conversion"]
"""
{
    "electrum": {"electrum":      1, "platinum":    10, "gold":  100, "silver": 1000, "copper": 10000},
    "platinum": {"electrum":    0.1, "platinum":     1, "gold":   10, "silver":  100, "copper":  1000},
    "gold":     {"electrum":   0.01, "platinum":   0.1, "gold":    1, "silver":   10, "copper":   100},
    "silver":   {"electrum":  0.001, "platinum":  0.01, "gold":  0.1, "silver":    1, "copper":    10},
    "copper":   {"electrum": 0.0001, "platinum": 0.001, "gold": 0.01, "silver":  0.1, "copper":     1}
}"""
# stores the players in the game
players = {}

# start the server
mud = MudServer()

# main game loop. We loop forever (i.e. until the program is terminated)
while True:
    # pause for 1/5 of a second on each loop, so that we don't constantly use 100% CPU time
    time.sleep(0.2)

    # 'update' must be called in the loop to keep the game running and give us up-to-date information
    mud.update()

    # go through any newly connected players
    for id in mud.get_new_players():
        # add the new player to the dictionary, noting that they've not been named yet. The dictionary key is the player's id number. We set their room to None initially until they have entered a name
        # Try adding more player stats - level, gold, inventory, etc
        players[id] = {
            "name": None,
            "money": data["defaults"]["money"],
            "inventory": [],
            "room": None,
        }

        # send the new player a prompt for their name
        mud.send_message(id, "What is your name?")
    # go through any recently disconnected players
    for id in mud.get_disconnected_players():
        # if for any reason the player isn't in the player map, skip them and move on to the next one
        if id not in players:
            continue
        # go through all the players in the game
        for pid, pl in players.items():
            # send each player a message to tell them about the diconnected player
            mud.send_message(pid, "{} quit the game".format(players[id]["name"]))
        # remove the player's entry in the player dictionary
        del(players[id])
    # go through any new commands sent from players
    for id, command, params in mud.get_commands():
        # if for any reason the player isn't in the player map, skip them and move on to the next one
        if id not in players:
            continue

        # if the player hasn't given their name yet, use this first command as their name and move them to the starting room.
        if players[id]["name"] is None:
            players[id]["name"] = command
            players[id]["room"] = data["defaults"]["location"] + ""

            # go through all the players in the game
            for pid, pl in players.items():
                # send each player a message to tell them about the new player
                mud.send_message(pid, "{} entered the game".format(players[id]["name"]))

            # send the new player a welcome message
            mud.send_message(id, "Welcome to the game, {}. ".format(players[id]["name"]) + "Type 'help' for a list of commands. Have fun!")

            # send the new player the description of their current room
            mud.send_message(id, rooms[players[id]["room"]]["description"])

        # each of the possible commands is handled below. Try adding new commands to the game!

        # 'help' command
        elif command == "help":
            # send the player back the list of possible commands
            mud.send_message(id, "Commands:")
            mud.send_message(id, "  say <message>  - Says something out loud, e.g. 'say Hello'")
            mud.send_message(id, "  look           - Examines the surroundings, e.g. 'look'")
            mud.send_message(id, "  go <exit>      - Moves through the exit specified, e.g. 'go outside'")
            mud.send_message(id, "  money [unit]   - Shows your balance. if no unit is specified, it lists all of them is short form.")
        # 'say' command
        elif command == "say":
            # go through every player in the game
            for pid, pl in players.items():
                # if they're in the same room as the player
                if players[pid]["room"] == players[id]["room"]:
                    # send them a message telling them what the player said
                    mud.send_message(pid, "{} says: {}".format(players[id]["name"], params))
        # 'look' command
        elif command == "look":
            # store the player's current room
            rm = rooms[players[id]["room"]]

            # send the player back the description of their current room
            mud.send_message(id, rm["description"])

            playershere = []
            # go through every player in the game
            for pid, pl in players.items():
                # if they're in the same room as the player
                if players[pid]["room"] == players[id]["room"]:
                    # ... and they have a name to be shown
                    if players[pid]["name"] is not None:
                        # add their name to the list
                        playershere.append(players[pid]["name"])

            # send player a message containing the list of players in the room
            mud.send_message(id, "Players here: {}".format(", ".join(playershere)))

            # send player a message containing the list of exits from this room
            mud.send_message(id, "Exits are: {}".format(", ".join(rm["exits"])))
        # 'go' command
        elif command == "go":
            # store the exit name
            ex = params.lower()

            # store the player's current room
            rm = rooms[players[id]["room"]]

            # if the specified exit is found in the room's exits list
            if ex in rm["exits"]:
                # go through all the players in the game
                for pid, pl in players.items():
                    # if player is in the same room and isn't the player sending the command
                    if players[pid]["room"] == players[id]["room"] and pid != id:
                        # send them a message telling them that the player left the room
                        mud.send_message(pid, "{} left via exit '{}'".format(players[id]["name"], ex))
                # update the player's current room to the one the exit leads to
                players[id]["room"] = rm["exits"][ex]
                rm = rooms[players[id]["room"]]

                # go through all the players in the game
                for pid, pl in players.items():
                    # if player is in the same (new) room and isn't the player sending the command
                    if players[pid]["room"] == players[id]["room"] \
                            and pid != id:
                        # send them a message telling them that the player entered the room
                        mud.send_message(pid, "{} arrived via exit '{}'".format( players[id]["name"], ex))
                # send the player a message telling them where they are now
                mud.send_message(id, "You arrive at '{}'".format(players[id]["room"]))
            # the specified exit wasn't found in the current room
            else:
                # send back an 'unknown exit' message
                mud.send_message(id, "Unknown exit '{}'".format(ex))
        # some other, unrecognised command
        elif command == "money":
            # give a amount of a certain type
            if params in players[id]["money"].keys():
                mud.send_message(id, "You have {} {} pieces".format(players[id]["money"][params], params))
            else:
                # show all curreency
                mud.send_message(id, "You have {} ep, {} pp, {} gp, {} sp, and {} cp".format(players[id]["money"]["electrum"], players[id]["money"]["platinum"], players[id]["money"]["gold"], players[id]["money"]["silver"], players[id]["money"]["copper"]))
        else :
            # send back an 'unknown command' message
            mud.send_message(id, "Unknown command '{}'".format(command))
