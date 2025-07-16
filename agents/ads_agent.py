# Файл: agents/ads_agent.py
from typing import List, Dict, Any

class AdsAgent:
    def __init__(self):
        print(" - AdsAgent (процессор) инициализирован.")

    def analyze(self, nm_id: int, full_ads_report: List[Dict[str, Any]]) -> dict:
        """Фильтрует общий список рекламных кампаний по nmId."""
        print(f"   [AdsAgent]: Поиск рекламы для nmId {nm_id}...")
        
        if "error" in full_ads_report:
            return full_ads_report
        
        relevant_ads = []
        for campaign in full_ads_report:
            # Проверяем, есть ли наш nm_id в списке 'nms' этой кампании
            if isinstance(campaign.get("params"), list):
                for param_set in campaign["params"]:
                    if nm_id in param_set.get("nms", []):
                        relevant_ads.append(campaign)
                        break # Достаточно одного совпадения на кампанию

        return {
    "active_campaigns_count": len(relevant_ads),
    "campaign_ids": [ad.get("advertId") for ad in relevant_ads],
    "campaign_names": [ad.get("name") for ad in relevant_ads if ad.get("name")],
    # Можно добавить другие параметры, если нужны
}