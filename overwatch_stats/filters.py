"""Filter option enumerations matching the dropdowns on overwatch.blizzard.com/en-us/rates."""

ROLES = ["All", "Tank", "Damage", "Support"]
INPUTS = ["PC", "Console"]
# rq = 0 -> Quick Play (Role Queue), rq = 2 -> Competitive (Role Queue)
RQS = ["0", "2"]
RQ_LABELS = {"0": "Quick Play", "2": "Competitive"}
TIERS = ["All", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster"]
MAPS = [
    "all-maps",
    "antarctic-peninsula", "busan", "ilios", "lijiang-tower", "nepal", "oasis", "samoa",
    "circuit-royal", "dorado", "havana", "junkertown", "rialto", "route-66",
    "shambali-monastery", "watchpoint-gibraltar", "aatlis", "new-junk-city", "suravasa",
    "blizzard-world", "eichenwalde", "hollywood", "kings-row", "midtown", "numbani",
    "paraiso", "colosseo", "esperanca", "new-queen-street", "runasapi",
]
REGIONS = ["Americas", "Asia", "Europe"]

DEFAULTS = {
    "role": "All",
    "input": "PC",
    "rq": "2",
    "tier": "All",
    "map": "all-maps",
    "region": "Europe",
}
