# 跨境电商订单异常识别与 AI 自动化处理系统

这是一个用于求职展示的 Web Demo，模拟跨境电商 ERP 订单同步后的异常识别、异常看板和 AI 处理建议。

## 运行方式

```powershell
cd E:\Administrator\Documents\cross-border-ai-order-assistant
python backend\app.py
```

打开浏览器访问：

```text
http://127.0.0.1:8765
```

## 功能

- 加载示例订单数据。
- 上传 CSV 订单数据。
- 识别物流、地址、电话、SKU、数量、金额、报关和状态异常。
- 展示异常率、异常类型分布和订单明细。
- 为单个异常订单生成 AI 处理建议和客服/运营话术。

## 目录

```text
backend/
  app.py
  rules.py
  ai_advisor.py
  sample_orders.csv
frontend/
  index.html
  style.css
  app.js
docs/
  PRD.md
  flow.md
  resume-description.md
  interview-script.md
```
