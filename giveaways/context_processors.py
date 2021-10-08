from .enums import GiveawayCategory, GiveawayStatus


def enums(request):
    return {"GiveawayStatus": GiveawayStatus, "GiveawayCategory": GiveawayCategory}
