from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class GateResult(str, Enum):
    RECOMMEND = "recommend"
    CONDITIONAL = "conditional"
    CAUTION = "caution"
    REFUSE = "refuse"


@dataclass
class SupplementDecision:
    result: GateResult
    action: str
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientSupplementContext:
    disclosed_conditions: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    age: Optional[int] = None
    pregnant: bool = False
    competes_in_tested_federation: bool = False
    lactose_intolerant: Optional[bool] = None
    anxiety_disorder_disclosed: bool = False
    goal: Optional[str] = None
