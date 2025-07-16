from pydantic import BaseModel, Field
from typing import List, Union, Literal, Dict, Optional
from enum import Enum
from datetime import date, timedelta

class Marketplace(str, Enum):
    WILDBERRIES = "wildberries"
    OZON = "ozon"
    YANDEX_MARKET = "yandex_market"

class Period(BaseModel):
    date_from: date
    date_to: date

class AnalysisRequest(BaseModel):
    marketplace: Marketplace
    # Заменяем старые поля на два новых объекта Period
    period_1: Period
    period_2: Period # Период, с которым будем сравнивать
    sku_list: Union[List[str], Literal["all"]]
    cost_prices: Optional[Dict[str, float]] = None

    class Config:
        arbitrary_types_allowed = True

class QuestionRequest(BaseModel):
    request_id: str
    sku: str
    aspect: Literal["sales", "card", "reviews", "ads", "profit", "audience"]
    question_text: str = "Расскажи подробнее об этом аспекте."
