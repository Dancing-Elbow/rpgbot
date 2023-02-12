import collections

import pymongo
from discord.ext import commands


class NoAccountCreatedError(commands.CommandError):
    pass


client = pymongo.MongoClient("mongodb+srv://DancingElbow:Sf4VzIuF56QmGTtb@allen.zm335vc.mongodb.net/?retryWrites"
                             "=true&w=majority")
database = client['information']
player_info = database['test']
soldier_time_info = database['soldier_time']


def reset():
    player_info.delete_many({})


def get_user_info(id):
    info = player_info.find_one({"_id": id})
    if info:
        return info
    raise NoAccountCreatedError


def inc_item(id, amount, *name):
    player_info.update_one({"_id": id}, {"$inc": {".".join(name): amount}})


def inc_item_dict(id, dict, *name):
    for k, v in dict.items():
        player_info.update_one({"_id": id}, {"$inc": {".".join(name) + "." + k: v}})


def get_dict(id, *name):
    info = get_user_info(id)
    for i in name:
        info = info[i]
    return info


def reach_goal(id, goal, *name):
    total = 0
    use = collections.defaultdict(int)
    info = get_dict(id, *name)
    keys = list(info.keys())
    keys.sort(reverse=True)
    for i in keys:
        amount = info[i]
        while total < goal and amount > 0:
            total += int(i)
            use[i] -= 1
            amount -= 1
    return dict(use), total


def compare_dict(id, dict, *name):
    info = get_dict(id, *name)
    all_lower = True
    all_higher = True
    for k, v in dict.items():
        if all_lower:
            all_lower = int(info[k]) > v
        if all_higher:
            all_higher = int(info[k]) < v
        if not all_lower and not all_higher:
            return 0
    if all_lower:
        return -1
    elif all_higher:
        return 1


def create_user(id):
    player_info.insert_one(
        {"_id": id, "soldiers_inv": {"horse_man": 0, "archer": 0, "foot_soldier": 0},
         "resources": {"wood": 0, "stone": 0, "ore": 0, "gold": 0, "crystalized_blood": 0},
         "resources_inv":
             {
                 "wood": {"10000": 0,
                          "100000": 0,
                          "500000": 0,
                          "1000000": 0},
                 "stone": {"10000": 0,
                           "100000": 0,
                           "500000": 0,
                           "1000000": 0},
                 "ore": {"10000": 0,
                         "100000": 0,
                         "500000": 0,
                         "1000000": 0},
                 "gold": {"5000": 0,
                          "20000": 0,
                          "100000": 0,
                          "500000": 0},
                 "crystalized_blood": {"50": 0,
                                       "100": 0,
                                       "500": 0,
                                       "1000": 0}}
         })
