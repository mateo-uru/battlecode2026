from body import DR, HOR_DRAFT

STUNNERS = {int(DR.RYTH), int(DR.STELLAR), int(DR.REN), int(DR.VARG), int(DR.TAVI), int(HOR_DRAFT)}

def preferences(info, size, ally, enemy):
    enemy_stuns = sum(1 for e in enemy if int(e) in STUNNERS)
    if size <= 3 and info.get("area", 2500) > 1200:
        return [DR.VARG, DR.TAVI, DR.VESPER_VALE, DR.VENDETTA, DR.CASSI_AND_ISSAC, DR.MARCELLA]
    if size == 4 and info.get("area", 2500) > 1200:
        return [DR.TAVI, DR.VESPER_VALE, DR.VENDETTA, DR.VARG, DR.CASSI_AND_ISSAC, DR.MARCELLA]
    if enemy_stuns >= 3 and len(ally) >= 3:
        return [DR.VARG, DR.VENDETTA, DR.RYTH, DR.MARCELLA, HOR_DRAFT, DR.REN, DR.CASSI_AND_ISSAC]
    return [DR.VARG, DR.VENDETTA, DR.RYTH, HOR_DRAFT, DR.REN, DR.CASSI_AND_ISSAC]
