"""g2_gobr: child of g1_goldrush and g1_brawler.

Genes: bank<-g1_goldrush, draft<-g1_brawler, extra<-g1_brawler, farm<-g1_brawler, fight<-g1_brawler, shop<-g1_goldrush, survive<-g1_goldrush, order<-g1_goldrush.

Gen-2 improvements against the parents' loss reasons: fight, survive and bank genes are the improved versions of the inherited parent genes (all visible enemies count, carriers back off, leave camp fights before the killing blow, shop recall, lower bank thresholds, bank when enemies are near); the farm gene avoids camps where enemies were just seen. Drafts Heart of Ruin instead of Marcella.
"""
import g_draft as DRAFT
import g_shop as SHOP
import g_extra as EXTRA
import g_bank
import g_farm
import g_fight
import g_survive

NAME = "g2_gobr"
ID = 9
GEN = 2
PARENTS = ['g1_goldrush', 'g1_brawler']
GENES = {"bank": g_bank, "farm": g_farm, "fight": g_fight, "survive": g_survive}
ORDER = ['survive', 'bank', 'fight', 'farm']
