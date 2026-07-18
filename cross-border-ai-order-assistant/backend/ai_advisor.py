from __future__ import annotations


ACTION_MAP = {
    "missing_logistics": "通知仓储或物流接口负责人补传物流单号，并在 ERP 中重新同步履约状态。",
    "address_incomplete": "联系客户补全详细街道、城市、邮编等字段，确认后重新生成面单。",
    "phone_invalid": "联系客户确认可用手机号，避免物流商拒收或派送失败。",
    "missing_sku": "回查平台订单明细和商品映射表，补全 SKU 后再进入拣货流程。",
    "quantity_invalid": "暂停履约，核对平台订单数量和支付记录，确认后修正订单数据。",
    "amount_invalid": "提交财务复核订单金额，确认是否为平台退款、优惠或同步异常。",
    "declaration_low": "交由报关/财务复核申报金额，避免低申报导致清关风险。",
    "status_conflict": "优先核查订单取消时间和物流揽收时间，必要时拦截包裹或通知客服安抚客户。",
    "tracking_delay": "查询物流商接口或人工刷新轨迹，超过 SLA 后升级给物流负责人。",
}


def build_advice(order: dict) -> dict:
    issues = order.get("issues", [])
    if not issues:
        return {
            "order_id": order.get("order_id"),
            "priority": "normal",
            "cause": "当前订单关键字段完整，物流与订单状态未发现明显冲突。",
            "actions": ["继续按正常履约流程处理。"],
            "message": "该订单目前未发现异常，可继续正常发货与跟踪。",
        }

    labels = "、".join(issue["label"] for issue in issues)
    actions = [ACTION_MAP.get(issue["code"], "安排运营人工复核该异常。") for issue in issues]
    priority = "urgent" if any(issue["severity"] == "high" for issue in issues) else "follow"
    owner = "运营负责人" if priority == "urgent" else "订单专员"

    message = (
        f"您好，订单 {order.get('order_id')} 当前存在{labels}问题。"
        "我们正在核对订单信息并尽快处理，处理完成后会同步最新进度。"
    )

    return {
        "order_id": order.get("order_id"),
        "priority": priority,
        "cause": f"系统识别到该订单存在 {labels}，可能影响发货、物流跟踪或报关核算。",
        "actions": actions,
        "owner": owner,
        "message": message,
    }
