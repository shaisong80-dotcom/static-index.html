from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


REQUIRED_FIELDS = [
    "order_id",
    "platform",
    "country",
    "customer_name",
    "phone",
    "address",
    "sku",
    "quantity",
    "order_amount",
    "declared_amount",
    "currency",
    "logistics_no",
    "order_status",
    "logistics_status",
    "created_at",
]


@dataclass(frozen=True)
class Issue:
    code: str
    label: str
    severity: str
    reason: str


def parse_csv(content: str) -> list[dict[str, str]]:
    stream = io.StringIO(content.strip())
    reader = csv.DictReader(stream)
    rows = []
    for row in reader:
        normalized = {field: (row.get(field) or "").strip() for field in REQUIRED_FIELDS}
        rows.append(normalized)
    return rows


def load_sample_orders(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return parse_csv(file.read())


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def detect_issues(order: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    phone = order.get("phone", "")
    address = order.get("address", "")
    sku = order.get("sku", "")
    logistics_no = order.get("logistics_no", "")
    order_status = order.get("order_status", "")
    logistics_status = order.get("logistics_status", "")
    quantity = _to_int(order.get("quantity", "0"))
    order_amount = _to_float(order.get("order_amount", "0"))
    declared_amount = _to_float(order.get("declared_amount", "0"))

    if not logistics_no:
        issues.append(Issue("missing_logistics", "物流单号缺失", "high", "已付款订单尚未生成物流单号，影响履约跟踪。"))

    if not address or len(address) < 12:
        issues.append(Issue("address_incomplete", "收件地址不完整", "high", "地址字段过短或为空，可能导致面单生成失败。"))

    if not phone or not re.fullmatch(r"\+?\d{7,15}", phone):
        issues.append(Issue("phone_invalid", "电话格式异常", "medium", "联系方式缺失或格式不符合跨境物流面单要求。"))

    if not sku:
        issues.append(Issue("missing_sku", "SKU 缺失", "high", "订单缺少 SKU，无法完成库存扣减和拣货。"))

    if quantity <= 0:
        issues.append(Issue("quantity_invalid", "数量异常", "high", "商品数量小于等于 0，需要回查平台订单。"))

    if order_amount <= 0:
        issues.append(Issue("amount_invalid", "订单金额异常", "high", "订单金额小于等于 0，可能影响财务核算。"))

    if order_amount > 0 and declared_amount > 0 and declared_amount / order_amount < 0.35:
        issues.append(Issue("declaration_low", "报关金额偏低", "medium", "申报金额明显低于订单金额，存在报关核算风险。"))

    if order_status == "Cancelled" and logistics_status in {"In transit", "Delivered"}:
        issues.append(Issue("status_conflict", "订单物流状态不一致", "high", "订单已取消但物流仍在运输或已签收，需要运营介入。"))

    if order_status == "Shipped" and logistics_status == "Pending":
        issues.append(Issue("tracking_delay", "物流轨迹未更新", "medium", "订单已发货但物流轨迹停留在待处理状态。"))

    return issues


def analyze_orders(orders: Iterable[dict[str, str]]) -> dict:
    analyzed = []
    issue_counter: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()

    for order in orders:
        issues = detect_issues(order)
        for issue in issues:
            issue_counter[issue.label] += 1
            severity_counter[issue.severity] += 1

        priority = "normal"
        if any(issue.severity == "high" for issue in issues):
            priority = "urgent"
        elif issues:
            priority = "follow"

        analyzed.append(
            {
                **order,
                "issues": [issue.__dict__ for issue in issues],
                "issue_count": len(issues),
                "priority": priority,
            }
        )

    total = len(analyzed)
    abnormal = sum(1 for order in analyzed if order["issue_count"])
    normal = total - abnormal
    abnormal_rate = round(abnormal / total * 100, 1) if total else 0

    return {
        "summary": {
            "total": total,
            "normal": normal,
            "abnormal": abnormal,
            "abnormal_rate": abnormal_rate,
            "urgent": severity_counter["high"],
            "follow": severity_counter["medium"],
        },
        "issue_distribution": [{"label": key, "count": value} for key, value in issue_counter.most_common()],
        "orders": analyzed,
    }
