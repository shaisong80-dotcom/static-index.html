const state = {
  data: null,
  filter: "all"
};

const $ = (selector) => document.querySelector(selector);

function priorityText(priority) {
  return {
    urgent: "高优先级",
    follow: "待跟进",
    normal: "正常"
  }[priority] || "正常";
}

function updateMetrics(summary) {
  $("#totalOrders").textContent = summary.total;
  $("#abnormalOrders").textContent = summary.abnormal;
  $("#abnormalRate").textContent = `${summary.abnormal_rate}%`;
  $("#urgentIssues").textContent = summary.urgent;
  $("#normalCount").textContent = `正常订单 ${summary.normal} 单`;
}

function renderChart(distribution) {
  const chart = $("#issueChart");
  if (!distribution.length) {
    chart.innerHTML = "<p>暂无异常类型。</p>";
    return;
  }
  const max = Math.max(...distribution.map((item) => item.count));
  chart.innerHTML = distribution.map((item) => {
    const width = Math.max(8, Math.round(item.count / max * 100));
    return `
      <div class="bar-row">
        <span>${item.label}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
        <strong>${item.count}</strong>
      </div>
    `;
  }).join("");
}

function filteredOrders() {
  if (!state.data) return [];
  if (state.filter === "all") return state.data.orders;
  return state.data.orders.filter((order) => order.priority === state.filter);
}

function renderRows() {
  const rows = filteredOrders();
  $("#orderRows").innerHTML = rows.map((order) => {
    const tags = order.issues.length
      ? order.issues.map((issue) => `<span class="tag">${issue.label}</span>`).join("")
      : `<span class="tag">无异常</span>`;
    const amount = `${order.order_amount} ${order.currency}`;
    return `
      <tr>
        <td>${order.order_id}</td>
        <td>${order.platform}</td>
        <td>${order.country}</td>
        <td>${amount}</td>
        <td>${order.order_status} / ${order.logistics_status}</td>
        <td><div class="tag-list">${tags}</div></td>
        <td class="priority ${order.priority}">${priorityText(order.priority)}</td>
        <td><button type="button" data-order="${order.order_id}">生成建议</button></td>
      </tr>
    `;
  }).join("");
}

function renderAll(data) {
  state.data = data;
  updateMetrics(data.summary);
  renderChart(data.issue_distribution);
  renderRows();
}

async function loadSample() {
  const response = await fetch("/api/orders");
  renderAll(await response.json());
}

async function uploadCsv(file) {
  const text = await file.text();
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "text/csv; charset=utf-8" },
    body: text
  });
  renderAll(await response.json());
}

async function showAdvice(orderId) {
  $("#advisorStatus").textContent = `订单 ${orderId}`;
  const order = state.data.orders.find((item) => item.order_id === orderId);
  const response = await fetch(`/api/advice?order_id=${encodeURIComponent(orderId)}`);
  const advice = await response.json();
  $("#adviceBox").classList.remove("empty");
  $("#adviceBox").innerHTML = `
    <div class="advice-section">
      <strong>异常原因</strong>
      <p>${advice.cause}</p>
    </div>
    <div class="advice-section">
      <strong>建议动作</strong>
      <ul>${advice.actions.map((action) => `<li>${action}</li>`).join("")}</ul>
    </div>
    <div class="advice-section">
      <strong>处理优先级</strong>
      <p>${priorityText(advice.priority)}，建议责任人：${advice.owner || "订单专员"}</p>
    </div>
    <div class="advice-section">
      <strong>客服/运营话术</strong>
      <p>${advice.message}</p>
    </div>
  `;
  if (order) order.selected = true;
}

$("#loadSample").addEventListener("click", loadSample);
$("#csvFile").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) uploadCsv(file);
});

document.addEventListener("click", (event) => {
  const orderId = event.target.dataset?.order;
  if (orderId) showAdvice(orderId);

  if (event.target.classList.contains("filter")) {
    document.querySelectorAll(".filter").forEach((button) => button.classList.remove("active"));
    event.target.classList.add("active");
    state.filter = event.target.dataset.filter;
    renderRows();
  }
});

loadSample();
