from body import DR, HOR_DRAFT

def preferences(info, size, ally, enemy):
    if size <= 4:
        return [DR.TAVI, DR.VESPER_VALE, DR.VENDETTA, DR.VARG, DR.CASSI_AND_ISSAC, DR.MARCELLA]
    return [DR.VARG, DR.VENDETTA, DR.RYTH, HOR_DRAFT, DR.REN, DR.CASSI_AND_ISSAC]
