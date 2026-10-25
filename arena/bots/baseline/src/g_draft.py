"""Draft gene (brawler): melee only."""
from body import DR, HOR_DRAFT


def preferences(info, size, ally, enemy):
    return [DR.VARG, DR.VENDETTA, DR.RYTH, HOR_DRAFT, DR.REN, DR.CASSI_AND_ISSAC]
