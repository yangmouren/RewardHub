const appState = {
  data: null,
  accounts: [],
  page: "home",
  selectedDate: localDate(),
  historyYear: new Date().getFullYear(),
  historyMonth: new Date().getMonth(),
  editorKind: null,
  editorId: null,
  selectedIcon: null,
  accountEditId: null,
  announcementEditId: null,
  announcementPopupTimer: null,
  // v0.13.0 长页面收纳：总览分 Tab、通知发布表单折叠、账户明细折叠、设置页分 Tab
  homeTab: "overview",
  settingsTab: "project",
  itemTab: "earn",
  announcementFormOpen: false,
  accountDetailOpen: false,
  // v0.13.2 账号管理页：每个账号一张可折叠卡片，这里记住哪些是展开的（重渲染后不丢）
  openAccounts: {},
  // v0.13.5 任务页：已完成任务折叠归档（展开状态）+ 批量删除的勾选项（存任务 id）
  questDoneOpen: false,
  pickedDoneTasks: [],
  // 冒险等级 / 积分换钱两个表单面板默认折叠（其余三个项目面板已改为 Tab 切换）
  settingsPanels: { level: false, currency: false },
};

let confirmResolver = null;

// 每日提交审核额度（v0.11.0）：0 = 不限制；后端默认值与此保持一致
const DEFAULT_SUBMIT_LIMIT = 10;
const MAX_SUBMIT_LIMIT = 999;

const CUSTOM_IMAGES = {
  "child-boy": { src: "/custom-assets/child-boy", fallback: "/static/avatars/boy.svg" },
  "child-girl": { src: "/custom-assets/child-girl", fallback: "/static/avatars/girl.svg" },
  "adult-male": { src: "/custom-assets/adult-male", fallback: "/static/avatars/adult-male.svg" },
  "adult-female": { src: "/custom-assets/adult-female", fallback: "/static/avatars/adult-female.svg" },
  "account-log": { src: "/custom-assets/account-log", fallback: "/static/illustrations/children-pair.svg" },
  "login-cover": { src: "/custom-assets/login-cover", fallback: "/static/illustrations/children-pair.svg" },
  "control-center": { src: "/static/custom/app-icon.png", fallback: "/static/illustrations/children-logo.svg" },
};
const AVATARS = {
  boy: { label: "男孩头像", ...CUSTOM_IMAGES["child-boy"], role: "child" },
  girl: { label: "女孩头像", ...CUSTOM_IMAGES["child-girl"], role: "child" },
  "adult-male": { label: "爸爸头像", ...CUSTOM_IMAGES["adult-male"], role: "admin" },
  "adult-female": { label: "妈妈头像", ...CUSTOM_IMAGES["adult-female"], role: "admin" },
};
const PROJECT_ICONS = [
  ["points.svg", "积分"], ["homework.svg", "作业"], ["book.svg", "阅读"],
  ["chore.svg", "家务"], ["sport.svg", "运动"], ["bedtime.svg", "早睡"],
  ["television.svg", "电视"], ["game.svg", "游戏"], ["snack.svg", "零食"],
  ["outing.svg", "外出"], ["gift.svg", "奖励"], ["warning.svg", "提醒"],
  ["computer.svg", "电脑"], ["desktop.svg", "桌面"], ["money.svg", "现金"],
  ["phone.svg", "手机"], ["cooking.svg", "做饭"], ["cleaning.svg", "清洁"],
  ["school.svg", "学校"], ["toothbrush.svg", "刷牙"], ["bath.svg", "洗澡"],
  ["pencil.svg", "学习"], ["clothes.svg", "穿衣"], ["laundry.svg", "洗衣"],
  ["dishes.svg", "洗碗"], ["pet.svg", "宠物"], ["walk.svg", "散步"],
  ["shopping.svg", "购物"], ["backpack.svg", "书包"], ["handwash.svg", "洗手"],
  ["water.svg", "喝水"], ["plant.svg", "植物"], ["tidy.svg", "收纳"],
  ["trash.svg", "垃圾"], ["lunch.svg", "午餐"],
  ["delivery.svg", "快递"],
];
const BUILTIN_ICON_GROUPS = [
  { name: "生活", items: [["home", "家", "\u{1F3E0}"], ["broom", "扫除", "\u{1F9F9}"], ["vacuum", "吸尘", "\u{1F9F9}"], ["clean", "清洁", "\u{1F9FD}"], ["tidy", "收纳", "\u{1F4E6}"], ["trash", "垃圾", "\u{1F5D1}"], ["laundry", "洗衣", "\u{1F455}"], ["dishes", "洗碗", "\u{1F37D}"], ["clothes", "穿衣", "\u{1F9E5}"], ["iron", "熨烫", "\u{1F9F4}"], ["bed", "床铺", "\u{1F6CF}"], ["sleep", "睡眠", "\u{1F634}"], ["alarm", "闹钟", "\u{23F0}"], ["shower", "淋浴", "\u{1F6BF}"], ["toothbrush", "刷牙", "\u{1FA95}"], ["handwash", "洗手", "\u{1F9FC}"], ["bath", "洗澡", "\u{1F6C1}"], ["repair", "维修", "\u{1F527}"], ["hammer", "锤子", "\u{1F528}"], ["screwdriver", "螺丝刀", "\u{1FA9B}"]] },
  { name: "饮食", items: [["cooking", "做饭", "\u{1F373}"], ["meal", "用餐", "\u{1F37D}"], ["breakfast", "早餐", "\u{1F305}"], ["lunch", "午餐", "\u{1F35B}"], ["dinner", "晚餐", "\u{1F958}"], ["bread", "面包", "\u{1F35E}"], ["rice", "米饭", "\u{1F35A}"], ["noodles", "面条", "\u{1F35C}"], ["apple", "苹果", "\u{1F34E}"], ["banana", "香蕉", "\u{1F34C}"], ["orange", "橙子", "\u{1F34A}"], ["strawberry", "草莓", "\u{1F353}"], ["cake", "蛋糕", "\u{1F382}"], ["cookie", "饼干", "\u{1F36A}"], ["milk", "牛奶", "\u{1F95B}"], ["water", "喝水", "\u{1F4A7}"], ["coffee", "咖啡", "\u{2615}"], ["tea", "茶", "\u{1F375}"], ["juice", "果汁", "\u{1F9C3}"], ["snack", "零食", "\u{1F36A}"], ["icecream", "冰淇淋", "\u{1F366}"]] },
  { name: "学习", items: [["homework", "作业", "\u{1F4DA}"], ["book", "阅读", "\u{1F4D6}"], ["reading", "深读", "\u{1F4D6}"], ["pencil", "写字", "\u{270F}"], ["school", "学校", "\u{1F3EB}"], ["graduation", "毕业", "\u{1F393}"], ["math", "数学", "\u{1F522}"], ["science", "科学", "\u{1F52C}"], ["language", "语言", "\u{1F5E3}"], ["art", "美术", "\u{1F3A8}"], ["music", "音乐", "\u{1F3B5}"], ["idea", "灵感", "\u{1F4A1}"], ["microscope", "实验", "\u{1F52C}"], ["ruler", "测量", "\u{1F4D0}"], ["notebook", "笔记", "\u{1F4D3}"], ["library", "图书馆", "\u{1F4DA}"], ["exam", "考试", "\u{1F4DD}"], ["medal", "勋章", "\u{1F3C5}"], ["target", "目标", "\u{1F3AF}"], ["lightbulb", "思考", "\u{1F4A1}"]] },
  { name: "运动", items: [["sport", "运动", "\u{1F3C3}"], ["run", "跑步", "\u{1F3C3}"], ["walk", "散步", "\u{1F6B6}"], ["bike", "骑行", "\u{1F6B4}"], ["swim", "游泳", "\u{1F3CA}"], ["football", "足球", "\u{26BD}"], ["basketball", "篮球", "\u{1F3C0}"], ["baseball", "棒球", "\u{26BE}"], ["tennis", "网球", "\u{1F3BE}"], ["badminton", "羽毛球", "\u{1F3F8}"], ["yoga", "瑜伽", "\u{1F9D8}"], ["weight", "力量", "\u{1F4AA}"], ["hiking", "徒步", "\u{1F97E}"], ["mountain", "登山", "\u{26F0}"], ["trophy", "奖杯", "\u{1F3C6}"], ["whistle", "裁判", "\u{1F3C1}"], ["skate", "滑冰", "\u{26F8}"], ["climbing", "攀岩", "\u{1F9D7}"], ["fitness", "健身", "\u{1F938}"], ["stretch", "拉伸", "\u{1F9D8}"]] },
  { name: "出行", items: [["car", "汽车", "\u{1F697}"], ["bus", "公交", "\u{1F68C}"], ["train", "火车", "\u{1F684}"], ["airplane", "飞机", "\u{2708}"], ["rocket", "火箭", "\u{1F680}"], ["ship", "轮船", "\u{1F6A2}"], ["taxi", "出租车", "\u{1F695}"], ["bicycle", "自行车", "\u{1F6B2}"], ["map", "地图", "\u{1F5FA}"], ["location", "定位", "\u{1F4CD}"], ["suitcase", "行李", "\u{1F9F3}"], ["passport", "护照", "\u{1F6C2}"], ["ticket", "票券", "\u{1F3AB}"], ["traffic", "交通", "\u{1F6A6}"], ["fuel", "加油", "\u{26FD}"], ["travel", "旅行", "\u{1F30D}"], ["compass", "指南针", "\u{1F9ED}"], ["road", "道路", "\u{1F6E3}"], ["parking", "停车", "\u{1F17F}"], ["delivery", "配送", "\u{1F4E6}"]] },
  { name: "家庭", items: [["family", "家庭", "\u{1F46A}"], ["child", "孩子", "\u{1F476}"], ["baby", "宝宝", "\u{1F476}"], ["adult", "大人", "\u{1F9D1}"], ["dog", "狗狗", "\u{1F436}"], ["cat", "猫咪", "\u{1F431}"], ["pet", "宠物", "\u{1F43E}"], ["plant", "植物", "\u{1F331}"], ["flower", "花朵", "\u{1F338}"], ["birthday", "生日", "\u{1F382}"], ["heart", "关爱", "\u{2764}"], ["homekey", "家门", "\u{1F511}"], ["door", "房门", "\u{1F6AA}"], ["sofa", "沙发", "\u{1F6CB}"], ["tv", "电视", "\u{1F4FA}"], ["camera", "拍照", "\u{1F4F7}"], ["phone", "电话", "\u{260E}"], ["calendar", "日历", "\u{1F4C5}"], ["couple", "陪伴", "\u{1F491}"], ["community", "社区", "\u{1F3D8}"]] },
  { name: "数码与 NAS", items: [["nas", "NAS", "\u{1F5A5}"], ["server", "服务器", "\u{1F5A5}"], ["harddrive", "硬盘", "\u{1F4BE}"], ["folder", "文件夹", "\u{1F4C1}"], ["cloud", "云端", "\u{2601}"], ["download", "下载", "\u{2B07}"], ["upload", "上传", "\u{2B06}"], ["wifi", "无线", "\u{1F4F6}"], ["network", "网络", "\u{1F310}"], ["database", "数据库", "\u{1F5C4}"], ["terminal", "终端", "\u{1F4BB}"], ["code", "代码", "\u{1F4BB}"], ["keyboard", "键盘", "\u{2328}"], ["printer", "打印", "\u{1F5A8}"], ["tablet", "平板", "\u{1F4F1}"], ["desktop", "桌面", "\u{1F5A5}"], ["computer", "电脑", "\u{1F4BB}"], ["smartphone", "手机", "\u{1F4F1}"], ["gamepad", "游戏", "\u{1F3AE}"], ["package", "包裹", "\u{1F4E6}"]] },
  { name: "工作与计划", items: [["office", "办公", "\u{1F3E2}"], ["briefcase", "工作", "\u{1F4BC}"], ["clock", "时间", "\u{23F1}"], ["chart", "图表", "\u{1F4C8}"], ["mail", "邮件", "\u{2709}"], ["meeting", "会议", "\u{1F465}"], ["call", "通话", "\u{1F4DE}"], ["checklist", "清单", "\u{1F4CB}"], ["pin", "标记", "\u{1F4CC}"], ["note", "便签", "\u{1F4DD}"], ["moneybag", "钱袋", "\u{1F4B0}"], ["contract", "合同", "\u{1F4C4}"], ["build", "建设", "\u{1F6E0}"], ["manager", "管理", "\u{1F9D1}"], ["megaphone", "广播", "\u{1F4E3}"], ["bell", "提醒", "\u{1F514}"], ["search", "搜索", "\u{1F50E}"], ["settings", "设置", "\u{2699}"], ["shield", "安全", "\u{1F6E1}"], ["lock", "锁定", "\u{1F512}"]] },
  { name: "奖励与收藏", items: [["coin", "积分", "\u{1FA99}"], ["money", "现金", "\u{1F4B5}"], ["diamond", "钻石", "\u{1F48E}"], ["crown", "皇冠", "\u{1F451}"], ["badge", "徽章", "\u{1F396}"], ["star", "星星", "\u{2B50}"], ["fire", "连胜", "\u{1F525}"], ["bolt", "能量", "\u{26A1}"], ["gem", "宝石", "\u{1F48E}"], ["treasure", "宝藏", "\u{1F5DD}"], ["giftbox", "礼物", "\u{1F381}"], ["fireworks", "烟花", "\u{1F386}"], ["crown2", "王冠", "\u{1F451}"], ["medal2", "奖章", "\u{1F3C5}"]] },
  { name: "健康", items: [["doctor", "医生", "\u{1F468}"], ["medicine", "药品", "\u{1F48A}"], ["hospital", "医院", "\u{1F3E5}"], ["mask", "口罩", "\u{1F637}"], ["bandage", "创可贴", "\u{1FA79}"], ["thermometer", "体温", "\u{1F321}"], ["apple2", "健康饮食", "\u{1F34E}"], ["water2", "补水", "\u{1F4A7}"], ["heart2", "心情", "\u{1F49A}"], ["brain", "大脑", "\u{1F9E0}"], ["lungs", "呼吸", "\u{1FAC1}"], ["health", "健康", "\u{2695}"], ["firstaid", "急救", "\u{1FA7A}"], ["rest", "休息", "\u{1F6CC}"]] },
  { name: "天气与自然", items: [["sun", "晴天", "\u{2600}"], ["moon", "月亮", "\u{1F319}"], ["cloud2", "多云", "\u{26C5}"], ["rain", "下雨", "\u{1F327}"], ["snow", "下雪", "\u{2744}"], ["rainbow", "彩虹", "\u{1F308}"], ["wind", "风", "\u{1F32C}"], ["leaf", "叶子", "\u{1F343}"], ["tree", "树木", "\u{1F333}"], ["flower2", "园艺", "\u{1F33B}"], ["season", "季节", "\u{1F342}"], ["umbrella", "雨具", "\u{2602}"], ["temperature", "温度", "\u{1F321}"], ["earth", "地球", "\u{1F30F}"]] },
  { name: "节日与社交", items: [["party", "派对", "\u{1F389}"], ["confetti", "庆祝", "\u{1F38A}"], ["balloon", "气球", "\u{1F388}"], ["cake2", "庆生", "\u{1F382}"], ["music2", "歌唱", "\u{1F3A4}"], ["flag", "旗帜", "\u{1F3F3}"], ["handshake", "合作", "\u{1F91D}"], ["speech", "发言", "\u{1F4AC}"], ["message", "消息", "\u{1F4E8}"], ["announcement", "通告", "\u{1F4E3}"], ["megaphone2", "通知", "\u{1F4E3}"], ["group", "小组", "\u{1F465}"], ["friend", "朋友", "\u{1F91D}"], ["smile", "心情好", "\u{1F60A}"]] },
];
const BUILTIN_ICON_MAP = new Map(BUILTIN_ICON_GROUPS.flatMap((group) => group.items.map(([key, label, emoji]) => [`emoji:${key}`, { key, label, emoji, category: group.name }])));
const DEFAULT_ITEM_ICONS = { earn: "points.svg", deduct: "warning.svg", reward: "gift.svg" };
const dayNames = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
const monthNames = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

function localDate(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);
}

function avatarSource(value) {
  return AVATARS[value]?.src || AVATARS.boy.src;
}

function avatarFallback(value) {
  return AVATARS[value]?.fallback || AVATARS.boy.fallback;
}

function setImageSource(element, source, fallback) {
  if (!element) return;
  element.onerror = () => {
    element.onerror = null;
    if (fallback) element.src = fallback;
  };
  element.src = source;
}

function avatarImage(value, className = "avatar avatar-small", alt = "") {
  return `<img class="${className}" src="${avatarSource(value)}" alt="${escapeHtml(alt)}" onerror="this.onerror=null;this.src='${avatarFallback(value)}'">`;
}

function illustrationSource(icon, kind = "earn") {
  const known = PROJECT_ICONS.some(([file]) => file === icon);
  const fallback = DEFAULT_ITEM_ICONS[kind === "exchange" ? "reward" : kind] || DEFAULT_ITEM_ICONS.earn;
  return `/static/illustrations/${known ? icon : fallback}`;
}

function iconMarkup(icon, kind = "earn", className = "project-visual") {
  const builtin = BUILTIN_ICON_MAP.get(icon);
  if (builtin) return `<span class="${className} project-emoji" title="${escapeHtml(builtin.label)}">${builtin.emoji}</span>`;
  return `<img class="${className}" src="${illustrationSource(icon, kind)}" alt="">`;
}

function itemIllustration(icon, kind) {
  return iconMarkup(icon, kind);
}

function signed(value) {
  const number = Number(value) || 0;
  return number > 0 ? `+${number}` : String(number);
}

function displayDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "暂无";
}

function recordsFor(date) {
  return (appState.data?.records || []).filter((record) => record.date === date);
}

function dayTotal(date) {
  return recordsFor(date).reduce((total, record) => total + Number(record.amount), 0);
}

function pointsRate() {
  return Number(appState.data?.settings?.points_per_yuan) > 0 ? Number(appState.data.settings.points_per_yuan) : 100;
}

function moneyFromPoints(points) {
  return (Number(points) || 0) / pointsRate();
}

function moneyText(points) {
  return `¥${moneyFromPoints(points).toFixed(2)}`;
}

function pointsText(points, includeMoney = true) {
  const value = Number(points) || 0;
  return includeMoney ? `${value.toLocaleString("zh-CN")} 积分 · ${moneyText(value)}` : `${value.toLocaleString("zh-CN")} 积分`;
}

function updateCurrencyUi() {
  const rate = pointsRate();
  const rule = document.getElementById("currency-rule");
  if (rule) rule.textContent = `${rate.toLocaleString("zh-CN")} 积分 = 1 元`;
  const input = document.querySelector("#currency-form input[name='points_per_yuan']");
  if (input && document.activeElement !== input) input.value = rate;
  const cashRate = document.getElementById("cash-exchange-rate");
  if (cashRate) cashRate.textContent = `当前比例：${rate.toLocaleString("zh-CN")} 积分 = 1 元`;
}

function levelBenefitText() {
  const gamification = appState.data?.gamification || {};
  const earnBonus = Number(gamification.earn_bonus_percent || 0);
  const exchangeDiscount = Number(gamification.exchange_discount_percent || 0);
  if (!earnBonus && !exchangeDiscount) return "";
  return "当前等级：赚积分 +" + earnBonus + "% · 兑换省 " + exchangeDiscount + "%";
}

function effectiveItemPoints(points, kind, mode) {
  const value = Math.abs(Number(points) || 0);
  if (mode !== "child") return value;
  const gamification = appState.data?.gamification || {};
  if (kind === "earn") return Math.max(1, Math.ceil(value * (1 + Number(gamification.earn_bonus_percent || 0) / 100)));
  if (kind === "exchange") return Math.max(1, Math.floor(value * (1 - Number(gamification.exchange_discount_percent || 0) / 100)));
  return value;
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error || "请求失败");
    error.status = response.status;
    throw error;
  }
  return payload;
}

// ---- 多设备同步（v0.10.0）----
// 典型场景是「家长手机发布任务、孩子平板查看」，孩子端必须能自己拿到最新数据，
// 不能只依赖整页刷新。切换页面 / 回到前台 / 定时都会静默拉一次最新状态。
let stateSyncAt = 0;
let stateSyncing = false;
const STATE_SYNC_MIN_INTERVAL = 3000;

async function syncState({ force = false } = {}) {
  if (!appState.data || stateSyncing) return;
  const elapsed = Date.now() - stateSyncAt;
  if (elapsed < 1000) return;                        // 同一瞬间（如 loadState 后紧跟导航）不重复请求
  if (!force && elapsed < STATE_SYNC_MIN_INTERVAL) return;
  stateSyncing = true;
  stateSyncAt = Date.now();
  try {
    const data = await api("/api/state", { cache: "no-store" });
    if (!data) return;
    appState.data = data;
    if (data.user?.role === "admin") appState.accounts = (await api("/api/accounts")).accounts;
    render();
  } catch (error) {
    // 静默失败：会话失效才切回登录页，其余交给顶栏连接指示器
    if (error.status === 401) showLogin();
  } finally {
    stateSyncing = false;
  }
}

async function loadState() {
  try {
    const setup = await api("/api/setup/status");
    if (!setup.configured) {
      showSetup();
      return;
    }
    appState.data = await api("/api/state");
    if (appState.data.user?.role === "admin") {
      appState.accounts = (await api("/api/accounts")).accounts;
    } else {
      appState.accounts = [];
    }
    stateSyncAt = Date.now();
    showApp();
    const initialHash = location.hash.replace(/^#/, "").trim();
    if (initialHash) appState.page = initialHash;
    navigate(appState.page);
  } catch (error) {
    if (error.status === 401) showLogin();
    else showToast(error.message);
  }
}

function showApp() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("setup-screen").classList.add("hidden");
  document.getElementById("child-register-screen").classList.add("hidden");
  document.getElementById("app-header").classList.remove("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  document.getElementById("bottom-nav").classList.remove("hidden");
  const indicator = document.getElementById("connection-state");
  if (indicator && !indicator.dataset.monitorReady) indicator.textContent = "连接中…";
}

function showLogin() {
  appState.data = null;
  appState.page = "home";
  closeModal();
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("setup-screen").classList.add("hidden");
  document.getElementById("child-register-screen").classList.add("hidden");
  document.getElementById("app-header").classList.add("hidden");
  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("bottom-nav").classList.add("hidden");
}

function showSetup() {
  appState.data = null;
  closeModal();
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("setup-screen").classList.remove("hidden");
  document.getElementById("child-register-screen").classList.add("hidden");
  document.getElementById("app-header").classList.add("hidden");
  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("bottom-nav").classList.add("hidden");
}

function showChildRegister() {
  appState.data = null;
  closeModal();
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("setup-screen").classList.add("hidden");
  document.getElementById("child-register-screen").classList.remove("hidden");
  document.getElementById("app-header").classList.add("hidden");
  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("bottom-nav").classList.add("hidden");
  document.querySelector("#child-register-form input[name='username']")?.focus();
}

function updateAccountUi() {
  const user = appState.data?.user;
  const isAdmin = user?.role === "admin";
  document.body.dataset.role = isAdmin ? "admin" : "child";
  document.querySelectorAll(".admin-only").forEach((element) => element.classList.toggle("hidden", !isAdmin));
  document.querySelectorAll(".child-only").forEach((element) => element.classList.toggle("hidden", isAdmin));
  document.getElementById("account-label").textContent = user ? `${user.display_name} · ${isAdmin ? "管理账号" : "孩子账号"}` : "";
  setImageSource(document.getElementById("user-avatar"), avatarSource(user?.avatar), avatarFallback(user?.avatar));
  const selector = document.getElementById("child-select");
  const children = appState.data.children || [];
  if (isAdmin) {
    selector.classList.toggle("hidden", !children.length);
    selector.innerHTML = children.map((child) => `<option value="${child.id}">${escapeHtml(child.display_name)}</option>`).join("");
    selector.value = String(appState.data.active_child_id || "");
  } else {
    selector.classList.add("hidden");
  }
}

function navigate(page) {
  const isAdmin = appState.data?.user?.role === "admin";
  if (page === "requests") page = "records";
  const adminPages = ["points", "accounts", "settings"];
  if (adminPages.includes(page) && !isAdmin) page = "home";
  if (page !== "quests" && appState.taskEditId) {
    appState.taskEditId = null;
    resetQuestForm();
  }
  appState.page = page;
  document.querySelectorAll(".page").forEach((element) => element.classList.toggle("active", element.dataset.page === page));
  document.querySelectorAll(".nav-button").forEach((element) => element.classList.toggle("active", element.dataset.pageTarget === page));
  render();
  // 任务页是「家长发布、孩子查看」跨设备刷新最敏感的地方，进入时强制同步一次
  syncState({ force: page === "quests" });
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (location.hash.slice(1) !== page) location.hash = page;
}

window.addEventListener("hashchange", () => {
  const page = location.hash.slice(1) || "home";
  if (page === appState.page) return;
  navigate(page);
});

let opKind = "earn";
function setOpKind(kind) {
  opKind = kind;
  const form = document.getElementById("points-form");
  if (!form) return;
  form.dataset.kind = kind;
  const submit = document.getElementById("points-submit");
  const nameInput = form.elements.name;
  if (kind === "earn") {
    submit.textContent = "确认加积分";
    submit.className = "button button-primary";
    nameInput.placeholder = "加积分说明，例如：完成作业";
  } else {
    submit.textContent = "确认扣积分";
    submit.className = "button button-danger";
    nameInput.placeholder = "扣积分说明，例如：未完成任务";
  }
  document.querySelectorAll(".operation-toggle .toggle-button").forEach((btn) => {
    const active = btn.dataset.opKind === kind;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", String(active));
  });
}

let itemKind = "earn";
function setItemKind(kind) {
  itemKind = kind;
  document.querySelectorAll("#items-toggle .toggle-button").forEach((btn) => {
    const active = btn.dataset.itemKind === kind;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", String(active));
  });
  document.getElementById("earn-items-panel")?.classList.toggle("hidden", kind !== "earn");
  document.getElementById("deduct-items-panel")?.classList.toggle("hidden", kind !== "deduct");
}

function render() {
  if (!appState.data) return;
  updateAccountUi();
  renderHome();
  renderHomeAdventure(appState.data);
  renderLevelBenefits(appState.data);
  renderHomeBroadcasts(appState.data);
  renderAdventureSettings(appState.data);
  renderEarnLists();
  renderDeductList();
  renderExchangeList();
  renderManagement();
  renderRequests();
  renderTaskReviews();
  renderQuests();
  renderQuestFocus();
  renderSubmitQuota();
  renderAnnouncements();
  renderAchievements();
  renderAccounts();
  renderRecords();
  updateCurrencyUi();
  updateCashExchangeDiscount();
  updateCashExchangePreview();
  applyTableLabels();
  syncHomeTabs();
  syncSettingsTabs();
  syncItemTabs();
  syncAnnouncementEditor();
  syncAccountDetail();
  syncSettingsPanels();
  detectCelebration(appState.data);
  setOpKind(opKind);
  setItemKind(itemKind);
}

// v0.12.0 长页面收纳 ----------
// 总览分区 Tab：角色不可用的 Tab（孩子端的「账户」）由 .admin-only 的 hidden 控制，
// 面板可见性只在这里统一决定，避免出现「Tab 被藏了但面板还露着」。
function syncHomeTabs() {
  const tabs = [...document.querySelectorAll("#home-tabs .home-tab")];
  if (!tabs.length) return;
  const available = tabs.filter((tab) => !tab.classList.contains("hidden"));
  const keys = available.map((tab) => tab.dataset.homeTab);
  if (!keys.includes(appState.homeTab)) appState.homeTab = keys[0] || "overview";
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.homeTab === appState.homeTab));
  document.querySelectorAll("[data-home-panel]").forEach((panel) => {
    panel.classList.toggle("panel-off", panel.dataset.homePanel !== appState.homeTab);
  });
}

// v0.13.0：设置页分区 Tab（项目设置 / 管理工具）。
// 只有 #settings-tabs 里的按钮参与「选中态」，所以每个 sync 都只查 Tab 栏，避免误伤普通按钮。
function syncSettingsTabs() {
  const tabs = [...document.querySelectorAll("#settings-tabs [data-settings-tab]")];
  const panels = [...document.querySelectorAll("[data-settings-tab-panel]")];
  if (!tabs.length && !panels.length) return;
  const keys = tabs.map((tab) => tab.dataset.settingsTab);
  if (keys.length && !keys.includes(appState.settingsTab)) appState.settingsTab = keys[0];
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.settingsTab === appState.settingsTab));
  panels.forEach((panel) => {
    panel.classList.toggle("panel-off", panel.dataset.settingsTabPanel !== appState.settingsTab);
  });
}

// v0.13.0：三个项目面板（加积分 / 扣积分 / 兑换奖励）改用 Tab 切换，不再折叠。
function syncItemTabs() {
  const tabs = [...document.querySelectorAll("#item-tabs [data-item-tab]")];
  if (!tabs.length) return;
  const keys = tabs.map((tab) => tab.dataset.itemTab);
  if (!keys.includes(appState.itemTab)) appState.itemTab = keys[0] || "earn";
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.itemTab === appState.itemTab));
  document.querySelectorAll("[data-item-tab-panel]").forEach((panel) => {
    panel.classList.toggle("panel-off", panel.dataset.itemTabPanel !== appState.itemTab);
  });
}

// 通知发布表单默认收起；进入编辑态时强制展开，否则找不到表单。
function syncAnnouncementEditor() {
  const editor = document.getElementById("announcement-editor");
  const toggle = document.getElementById("toggle-announcement-editor");
  if (!editor || !toggle) return;
  const open = Boolean(appState.announcementFormOpen) || Boolean(appState.announcementEditId);
  editor.classList.toggle("is-collapsed", !open);
  toggle.textContent = open ? "收起发布框" : "＋ 发布通知";
  toggle.setAttribute("aria-expanded", String(open));
}

// 账户明细列（折合金额 / 今日变化 / 状态）默认收起，只留账户、当前积分、待审核。
function syncAccountDetail() {
  const table = document.getElementById("home-account-table");
  const toggle = document.getElementById("toggle-account-detail");
  if (!table || !toggle) return;
  const open = Boolean(appState.accountDetailOpen);
  table.classList.toggle("is-compact", !open);
  toggle.textContent = open ? "收起明细" : "展开明细";
  toggle.setAttribute("aria-expanded", String(open));
}

// 冒险等级 / 积分换钱两个表单面板折叠（v0.13.0 起只有这两个还用折叠）。
function syncSettingsPanels() {
  document.querySelectorAll("[data-settings-panel]").forEach((panel) => {
    const open = Boolean(appState.settingsPanels[panel.dataset.settingsPanel]);
    const list = panel.querySelector(".item-list");
    const count = panel.querySelectorAll(".item-list .list-row").length;
    // 空的项目面板自动展开：只有一行「暂无项目」提示，撑不长页面，还能直接引导新增。
    // 等级 / 换钱两个表单面板没有 .item-list，始终跟随 appState。
    const effectiveOpen = open || (Boolean(list) && count === 0);
    panel.classList.toggle("is-collapsed", !effectiveOpen);
    const toggle = panel.querySelector("[data-toggle-settings-panel]");
    if (!toggle) return;
    toggle.textContent = effectiveOpen ? "收起" : list ? `展开 · ${count} 项` : "展开";
    toggle.setAttribute("aria-expanded", String(effectiveOpen));
  });
}

function activeAccount() {
  if (appState.data?.active_child) return appState.data.active_child;
  return appState.data?.user?.role === "child" ? appState.data.user : {};
}

function renderHome() {
  const data = appState.data;
  const user = data.user;
  const account = activeAccount();
  const hasChild = Boolean(account.id);
  const today = localDate();
  const todayRecords = recordsFor(today);
  const income = todayRecords.filter((record) => record.type === "income").reduce((sum, record) => sum + Number(record.amount), 0);
  const expense = Math.abs(todayRecords.filter((record) => record.type === "expense").reduce((sum, record) => sum + Number(record.amount), 0));
  const children = (data.account_overview || []).filter((item) => item.role === "child");
  // v0.10.1：待办口径 = 积分申请(pending_count) + 任务验收(task_pending_count)，与「审核中心」一致
  const childPending = (item) => Number(item.pending_count) + Number(item.task_pending_count || 0);
  const pending = children.reduce((sum, item) => sum + childPending(item), 0);
  const weekTotal = dayNames.reduce((sum, _, index) => {
    const current = new Date();
    const day = current.getDay() || 7;
    current.setDate(current.getDate() - day + index + 1);
    return sum + dayTotal(localDate(current));
  }, 0);
  document.getElementById("home-title").textContent = user.role === "admin" ? (hasChild ? "家庭监控总控" : "先创建孩子账号") : "我的积分空间";
  document.getElementById("home-subtitle").textContent = user.role === "admin" ? (hasChild ? "总览积分、审批和账户状态，快速执行家庭规则" : "当前还没有孩子账号，请先到账号管理创建") : "完成任务后申请积分，等待家长审核到账";
  document.getElementById("today-label").textContent = today;
  setImageSource(
    document.getElementById("active-avatar"),
    account.avatar ? avatarSource(account.avatar) : CUSTOM_IMAGES["control-center"].src,
    account.avatar ? avatarFallback(account.avatar) : CUSTOM_IMAGES["control-center"].fallback,
  );
  document.getElementById("active-name").textContent = account.display_name || "暂无孩子账号";
  document.getElementById("active-username").textContent = account.username ? `账号：${account.username}` : "";
  document.getElementById("active-account-kicker").textContent = user.role === "admin" ? "当前操作对象" : "我的账号";
  document.getElementById("total-points").textContent = Number(data.total_points || 0).toLocaleString("zh-CN");
  document.getElementById("total-money").textContent = `折合 ${moneyText(data.total_points)}`;
  document.getElementById("points-target-name").textContent = account.display_name || "暂无孩子账号";
  document.getElementById("pending-action-label").textContent = `${pending} 条待处理`;
  document.querySelector(".hero-actions.admin-only")?.classList.toggle("hidden", user.role !== "admin" || !hasChild);
  document.getElementById("no-child-panel")?.classList.toggle("hidden", !(user.role === "admin" && !hasChild));
  const familyPoints = children.reduce((sum, item) => sum + Number(item.total_points), 0);
  const metrics = user.role === "admin" ? [
    ["孩子账户", children.length, "个", "metric-green"],
    // v0.12.0：banner 里那组重复的合计卡已删，折合金额并进这张卡的单位位，信息不丢
    ["家庭总积分", familyPoints.toLocaleString("zh-CN"), moneyText(familyPoints), "metric-blue"],
    ["待审核事项", pending, "条", pending ? "metric-orange" : "metric-green"],
    ["本周变化", signed(weekTotal), "积分", weekTotal >= 0 ? "metric-green" : "metric-red"],
  ] : [
    ["今日赚取积分", income, "分", "metric-green"],
    ["今日扣除积分", expense, "分", "metric-red"],
    ["今日净增积分", signed(income - expense), "分", income >= expense ? "metric-blue" : "metric-orange"],
    ["待审核申请", (data.requests || []).filter((item) => item.status === "pending").length, "条", "metric-orange"],
  ];
  document.getElementById("home-metrics").innerHTML = metrics.map(([label, value, unit, color]) => `<div class="metric-card ${color}"><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${unit}</small></div>`).join("");
  const controlTitle = document.getElementById("control-center-title");
  const controlSubtitle = document.getElementById("control-center-subtitle");
  const controlChildCount = document.getElementById("control-child-count");
  const controlTotalPoints = document.getElementById("control-total-points");
  const controlPendingCount = document.getElementById("control-pending-count");
  if (controlTitle) controlTitle.textContent = hasChild ? `${account.display_name} 的积分中枢` : "家庭积分中枢";
  if (controlSubtitle) controlSubtitle.textContent = hasChild ? `当前监控 ${account.username || "孩子账号"}，可立即执行家庭规则` : "先创建孩子账号，再开始家庭积分管理";
  if (controlChildCount) controlChildCount.textContent = children.length;
  if (controlTotalPoints) controlTotalPoints.textContent = children.reduce((sum, item) => sum + Number(item.total_points), 0).toLocaleString("zh-CN");
  if (document.getElementById("control-total-money")) document.getElementById("control-total-money").textContent = moneyText(children.reduce((sum, item) => sum + Number(item.total_points), 0));
  if (controlPendingCount) controlPendingCount.textContent = pending;
  const homeSummary = document.getElementById("home-account-summary");
  if (homeSummary) {
    homeSummary.innerHTML = children.length ? children.map((child) => { const childTotal = childPending(child); return `<tr><td><div class="table-person">${avatarImage(child.avatar, "avatar avatar-table", child.display_name)}<div><strong>${escapeHtml(child.display_name)}</strong><small>${escapeHtml(child.username)}</small></div></div></td><td class="table-number">${Number(child.total_points).toLocaleString("zh-CN")}</td><td class="table-number account-detail">${moneyText(child.total_points)}</td><td class="table-number account-detail ${Number(child.today_net) >= 0 ? "income" : "expense"}">${signed(child.today_net)}</td><td><span class="pending-badge">${childTotal}</span></td><td class="account-detail"><span class="status-pill ${childTotal ? "status-pending" : "status-approved"}">${childTotal ? "待审核" : "运行正常"}</span></td></tr>`; }).join("") : `<tr><td colspan="6"><div class="empty-state">暂无孩子账号，请先创建账号</div></td></tr>`;
  }
  renderWeekGrid(document.getElementById("home-week-grid"), "home-week-title");
  const preview = document.getElementById("home-request-preview");
  const recent = (data.requests || []).slice(0, 3);
  preview.innerHTML = recent.length ? recent.map(requestMarkup).join("") : `<div class="empty-state">暂无申请记录</div>`;
}

function renderHomeAdventure(data) {
  const gamification = data.gamification || {};
  const level = Number(gamification.level || 1);
  const experience = Number(gamification.experience || 0);
  const next = Number(gamification.next_level_exp || level * 100);
  const levelElement = document.getElementById("home-level");
  if (!levelElement) return;
  levelElement.textContent = level;
  document.getElementById("home-level-name").textContent = "冒险者等级 " + level;
  document.getElementById("home-level-xp").textContent = experience + " / " + next + " XP";
  document.getElementById("home-level-progress").style.width = Math.min(100, Math.max(0, experience % 100)) + "%";
  document.getElementById("home-level-mode").textContent = levelBenefitText() || (gamification.level_mode === "manual" ? "管理员已手动设置当前等级" : "根据任务经验自动计算");
  document.getElementById("home-completed-tasks").textContent = Number(gamification.completed_tasks || 0).toLocaleString("zh-CN");
  document.getElementById("home-unlocked-achievements").textContent = Number(gamification.unlocked_achievements || 0).toLocaleString("zh-CN");
}

function renderLevelBenefits(data) {
  const levelElement = document.getElementById("exchange-benefit-level");
  if (!levelElement) return;
  const gamification = data.gamification || {};
  const level = Math.max(1, Number(gamification.level || 1));
  const earnBonus = Number(gamification.earn_bonus_percent || 0);
  const exchangeDiscount = Number(gamification.exchange_discount_percent || 0);
  const nextLevel = level + 1;
  const nextEarnBonus = Math.min(Math.max(nextLevel - 1, 0), 20) * 5;
  const nextExchangeDiscount = Math.min(Math.max(nextLevel - 1, 0), 20) * 2.5;
  levelElement.textContent = level;
  document.getElementById("exchange-earn-benefit").textContent = `+${earnBonus}%`;
  document.getElementById("exchange-discount-benefit").textContent = `省 ${exchangeDiscount}%`;
  document.getElementById("exchange-next-benefit").textContent = `下一等级 LV ${nextLevel}`;
  document.getElementById("exchange-next-text").textContent = `赚积分 +${nextEarnBonus}% · 兑换省 ${nextExchangeDiscount}%`;
}

function renderHomeBroadcasts(data) {
  const taskList = document.getElementById("home-task-list");
  if (taskList) {
    const tasks = (data.tasks || []).slice(0, 4);
    taskList.innerHTML = tasks.length ? tasks.map(function (task) {
      const rewardCoins = Number(task.reward_coins);
      const baseReward = Number(task.base_reward_coins || rewardCoins);
      const rewardNote = baseReward !== rewardCoins ? '<small>基础 ' + baseReward.toLocaleString("zh-CN") + '</small>' : '';
      return '<button class="home-task-row" data-page-target="quests" type="button"><span class="home-task-icon">' + iconMarkup(task.icon, "earn", "home-task-visual") + '</span><span class="home-task-copy"><strong>' + escapeHtml(task.title) + '</strong><small>' + escapeHtml(TASK_TYPE_TEXT[task.task_type] || task.task_type) + ' · ' + escapeHtml(TASK_DIFFICULTY_TEXT[task.difficulty] || task.difficulty) + '</small></span><span class="home-task-reward">' + rewardCoins.toLocaleString("zh-CN") + ' 积分' + rewardNote + '</span></button>';
    }).join("") : '<div class="empty-state">暂无已发布任务</div>';
  }
}

function renderAdventureSettings(data) {
  const form = document.getElementById("adventure-level-form");
  if (!form) return;
  const settings = data.settings || {};
  const manual = settings.adventure_level_mode === "manual";
  form.elements.mode.value = manual ? "manual" : "auto";
  form.elements.level.value = manual ? settings.manual_adventure_level : (data.gamification?.level || 1);
  form.elements.level.disabled = !manual;
  // 折叠状态下也要能看到当前等级配置
  const summary = document.getElementById("adventure-level-summary");
  if (summary) {
    summary.textContent = manual
      ? `手动指定：LV ${settings.manual_adventure_level}`
      : `自动计算：LV ${data.gamification?.level || 1}（按任务经验）`;
  }
}

function renderEarnLists() {
  renderItemList(document.getElementById("earn-list"), appState.data.earn_items || [], "earn", "admin");
  renderItemList(document.getElementById("child-earn-list"), appState.data.earn_items || [], "earn", "child");
}

function renderDeductList() {
  renderItemList(document.getElementById("deduct-list"), appState.data.deduct_items || [], "deduct", "admin");
}

function renderExchangeList() {
  renderItemList(document.getElementById("exchange-list"), appState.data.rewards || [], "exchange", "child");
}

function renderItemList(container, items, kind, mode) {
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-state">暂无项目，请先在项目设置中添加。</div>`;
    return;
  }
  const isExchange = kind === "exchange";
  const actionText = isExchange ? "申请兑换" : mode === "child" ? "申请" : kind === "earn" ? "加积分" : "扣积分";
  const actionClass = kind === "deduct" ? "button-danger" : isExchange ? "button-dark" : "button-primary";
  const pointSign = kind === "deduct" || isExchange ? "-" : "+";
  container.innerHTML = items.map((item) => {
    const basePoints = Number(item.base_points || Math.abs(Number(item.points)));
    const actualPoints = Math.abs(Number(item.points));
    const benefitNote = mode === "child" && basePoints !== actualPoints ? `<small class="benefit-note">基础 ${basePoints.toLocaleString("zh-CN")} 积分</small>` : "";
    return `<div class="list-row"><div class="item-info"><div class="project-visual-wrap">${itemIllustration(item.icon, kind)}</div><div><strong>${escapeHtml(item.name)}</strong><span class="item-points ${kind === "deduct" || isExchange ? "expense" : "income"}">${pointSign}${pointsText(actualPoints)}</span>${benefitNote}</div></div><button class="button button-small ${actionClass}" data-action="${kind}" data-id="${item.id}" type="button">${actionText}</button></div>`;
  }).join("");
}

function renderManagement() {
  renderManageList("earn-manage-list", appState.data.earn_items || [], "earn");
  renderManageList("deduct-manage-list", appState.data.deduct_items || [], "deduct");
  renderManageList("reward-manage-list", appState.data.rewards || [], "reward");
}

function renderManageList(elementId, items, kind) {
  const container = document.getElementById(elementId);
  if (!container) return;
  const isExpense = kind === "deduct" || kind === "reward";
  container.innerHTML = items.length ? items.map((item) => `<div class="list-row"><div class="item-info"><div class="project-visual-wrap">${itemIllustration(item.icon, kind)}</div><div><strong>${escapeHtml(item.name)}</strong><span class="item-points ${isExpense ? "expense" : "income"}">${isExpense ? "-" : "+"}${pointsText(Math.abs(Number(item.points)))}</span></div></div><div class="row-actions"><button class="button button-small button-outline" data-action="edit" data-kind="${kind}" data-id="${item.id}" type="button">编辑</button><button class="button button-small button-outline-danger" data-action="delete" data-kind="${kind}" data-id="${item.id}" type="button">删除</button></div></div>`).join("") : `<div class="empty-state">暂无项目</div>`;
}

function requestMarkup(request) {
  const statusText = { pending: "待审核", approved: "已通过", rejected: "已拒绝" };
  const kindText = { earn: "赚取积分申请", exchange: "兑换申请", cash_exchange: "现金兑换", deduct: "扣积分申请", manual: "补录积分申请" };
  const status = request.status || "pending";
  const childAvatar = request.child_avatar || "boy";
  const action = appState.data.user.role === "admin" && status === "pending" ? `<div class="row-actions"><button class="button button-small button-primary" data-action="approve-request" data-id="${request.id}" type="button">通过</button><button class="button button-small button-outline-danger" data-action="reject-request" data-id="${request.id}" type="button">拒绝</button></div>` : `<span class="status-pill status-${status}">${statusText[status] || status}</span>`;
  return `<div class="request-row"><div class="request-person">${avatarImage(childAvatar, "avatar avatar-small", request.child_name || "孩子")}<div><strong>${escapeHtml(kindText[request.kind] || "积分申请")}：${escapeHtml(request.title)}</strong><span>${appState.data.user.role === "admin" ? `${escapeHtml(request.child_name || "孩子")} · ` : ""}${escapeHtml(request.date)} ${escapeHtml(request.time)}</span>${status === "rejected" && request.reject_reason ? `<em>${escapeHtml(request.reject_reason)}</em>` : ""}</div></div><strong class="request-amount ${Number(request.amount) >= 0 ? "income" : "expense"}">${signed(request.amount)} 积分</strong>${action}</div>`;
}

function renderRequests() {
  const isAdmin = appState.data.user.role === "admin";
  document.getElementById("requests-title").textContent = isAdmin ? "积分申请" : "我的申请";
  document.getElementById("requests-subtitle").textContent = isAdmin ? "孩子提交的赚积分或兑换申请，审核后才会更新余额。" : "申请不会直接改变余额，等待管理账号审核。";
  const requests = appState.data.requests || [];
  document.getElementById("requests-list").innerHTML = requests.length ? requests.map(requestMarkup).join("") : `<div class="empty-state">暂无申请记录</div>`;
}

// v0.10.1：管理端「审核中心」的任务验收队列。
// 此前孩子提交验收后，管理端只能到任务页每张卡片的人员小列表里逐个点，缺少集中的待办入口，
// 于是「记录页看不到需要审核的」。这里把 status='submitted' 的提交汇总成一条待办列表，
// 复用任务页已有的 approve-task / reject-task 动作。
function taskReviewMarkup(review) {
  const childName = review.child_name || "孩子";
  const submitted = String(review.submitted_at || "");
  const submittedTime = submitted.length >= 16 ? submitted.slice(11, 16) : "";
  const withdrawn = review.task_active === false ? " · 任务已撤下" : "";
  return `<div class="request-row"><div class="request-person">${avatarImage(review.child_avatar || "boy", "avatar avatar-small", childName)}<div><strong>任务验收：${escapeHtml(review.task_title)}</strong><span>${escapeHtml(childName)} · ${escapeHtml(review.claim_date)}${submittedTime ? ` ${escapeHtml(submittedTime)}` : ""} 提交${withdrawn}</span></div></div><strong class="request-amount income">${signed(review.reward_coins)} 积分</strong><div class="row-actions"><button class="button button-small button-primary" data-action="approve-task" data-id="${review.assignment_id}" type="button">通过</button><button class="button button-small button-outline-danger" data-action="reject-task" data-id="${review.assignment_id}" type="button">重做</button></div></div>`;
}

function renderTaskReviews() {
  const list = document.getElementById("task-review-list");
  if (!list) return;
  const reviews = appState.data.task_reviews || [];
  const pendingRequests = (appState.data.requests || []).filter((request) => (request.status || "pending") === "pending").length;
  const subtitle = document.getElementById("review-subtitle");
  if (appState.data.user.role === "admin") {
    document.getElementById("task-review-title").textContent = reviews.length ? `任务验收（${reviews.length}）` : "任务验收";
    document.getElementById("task-review-subtitle").textContent = reviews.length ? "孩子已完成、等待你验收的任务。" : "当前没有等待验收的任务提交。";
    if (subtitle) subtitle.textContent = reviews.length || pendingRequests ? `待处理：任务验收 ${reviews.length} 项 · 积分申请 ${pendingRequests} 项。` : "当前没有待处理的审核事项。";
  } else if (subtitle) {
    subtitle.textContent = "查看积分的每日变化，以及你提交的申请进度。";
  }
  list.innerHTML = reviews.length ? reviews.map(taskReviewMarkup).join("") : `<div class="empty-state">暂无待验收的任务</div>`;
}

const TASK_DIFFICULTY_TEXT = { easy: "简单", normal: "普通", hard: "困难", legendary: "传说" };
const TASK_TYPE_TEXT = { daily: "日常任务", repeat: "重复任务", epic: "史诗悬赏" };
const TASK_STATUS_TEXT = { claimed: "已领取", submitted: "待验收", completed: "已完成", rejected: "需重做" };

function taskActionMarkup(task) {
  const isAdmin = appState.data.user.role === "admin";
  if (isAdmin) {
    const pending = (task.assignments || []).filter((assignment) => assignment.status === "submitted");
    const status = pending.length ? `<span class="quest-status quest-status-submitted">${pending.length} 人待验收</span>` : `<span class="muted">${task.participant_count || 0} 人参与</span>`;
    // v0.13.2：已有「审核通过」的提交后，任务规则已生效，不允许再编辑（服务端同样拦截）。
    const editButton = task.edit_locked
      ? `<span class="quest-status quest-status-completed" title="已有审核通过的提交，任务规则不能再修改">已验收 · 不可编辑</span>`
      : `<button class="button button-small button-outline" data-action="edit-task" data-id="${task.id}" type="button">编辑</button>`;
    return `<div class="row-actions">${status}${editButton}<button class="button button-small button-outline-danger" data-action="delete-task" data-id="${task.id}" type="button">删除</button></div>`;
  }
  // 重复任务今天不触发、但计划还没结束：提前告诉孩子下次什么时候开始，且不可领取
  if (task.task_type === "repeat" && task.active_today === false) {
    const next = String(task.next_date || "").slice(5);
    return `<span class="quest-status quest-status-upcoming">未开始${next ? ` · 下次 ${escapeHtml(next)}` : ""}</span>`;
  }
  const assignment = task.my_assignment;
  if (!assignment) return `<button class="button button-small button-primary" data-action="claim-task" data-id="${task.id}" type="button">领取任务</button>`;
  if (assignment.status === "claimed" || assignment.status === "rejected") return `<button class="button button-small ${assignment.status === "rejected" ? "button-danger" : "button-dark"}" data-action="submit-task" data-id="${assignment.id}" type="button">${assignment.status === "rejected" ? "重新提交" : "提交验收"}</button>`;
  return `<span class="quest-status quest-status-${assignment.status}">${TASK_STATUS_TEXT[assignment.status] || assignment.status}</span>`;
}

function questAssignmentMarkup(assignment) {
  const isPending = assignment.status === "submitted";
  const controls = isPending ? `<div class="row-actions"><button class="button button-small button-primary" data-action="approve-task" data-id="${assignment.id}" type="button">通过</button><button class="button button-small button-outline-danger" data-action="reject-task" data-id="${assignment.id}" type="button">重做</button></div>` : `<span class="quest-status quest-status-${assignment.status}">${TASK_STATUS_TEXT[assignment.status] || assignment.status}</span>`;
  return `<div class="quest-assignee"><span>${escapeHtml(assignment.account_name)} · ${escapeHtml(assignment.claim_date)}</span>${controls}</div>`;
}

function questCardMarkup(task, options = {}) {
  const { done = false } = options;
  const isAdmin = appState.data.user.role === "admin";
  const assignments = isAdmin && task.assignments?.length ? `<div class="quest-assignees">${task.assignments.map(questAssignmentMarkup).join("")}</div>` : "";
  const rewardCoins = Number(task.reward_coins);
  const baseReward = Number(task.base_reward_coins || rewardCoins);
  const rewardNote = baseReward !== rewardCoins ? `<small class="quest-reward-note">基础 ${baseReward.toLocaleString("zh-CN")}</small>` : "";
  const isRepeat = task.task_type === "repeat";
  const pausedToday = isRepeat && !task.active_today;
  // 「今日不触发」是管理视角的提示；孩子端由操作区的「未开始 · 下次 X」表达，避免重复
  const restChip = pausedToday && isAdmin ? `<span class="quest-rest">今日不触发</span>` : "";
  const metaRight = isRepeat
    ? `<span class="quest-repeat">↻ ${escapeHtml(task.repeat_text || "重复任务")}</span>${restChip}`
    : `<span class="muted">${task.due_date ? `截止 ${escapeHtml(task.due_date)}` : "长期有效"}</span>`;
  // v0.13.5：归档里的卡片给管理端一个勾选框，用于批量删除
  const pick = done && isAdmin
    ? `<label class="quest-pick" title="勾选后可批量删除"><input type="checkbox" data-pick-task="${task.id}"${appState.pickedDoneTasks.includes(Number(task.id)) ? " checked" : ""}></label>`
    : "";
  return `<article class="quest-card${task.task_type === "epic" ? " epic" : ""}${isRepeat ? " repeat" : ""}${pausedToday ? " resting" : ""}${done ? " is-done" : ""}"><div class="quest-card-head">${pick}<div class="quest-card-title">${iconMarkup(task.icon, "earn", "quest-icon") }<div><h2>${escapeHtml(task.title)}</h2><p>${escapeHtml(task.category)} · ${TASK_TYPE_TEXT[task.task_type] || task.task_type}</p></div></div><span class="quest-rarity">${TASK_DIFFICULTY_TEXT[task.difficulty] || task.difficulty}</span></div><p class="quest-description">${escapeHtml(task.description || "完成任务后提交，等待管理员验收。")}</p><div class="quest-card-meta"><span class="quest-reward">◆ ${rewardCoins.toLocaleString("zh-CN")} 积分${rewardNote}</span><span class="quest-reward">✦ ${Number(task.reward_exp).toLocaleString("zh-CN")} XP</span>${metaRight}</div><div class="quest-card-actions">${taskActionMarkup(task)}</div>${assignments}</article>`;
}

// v0.13.5：已完成任务折叠归档 —— 管理端=该任务的全部提交都已验收、没有进行中的；
// 孩子端=最近一次提交已通过。归档默认收起，展开后管理端可勾选批量删除。
function questDoneSection(doneTasks) {
  const isAdmin = appState.data.user.role === "admin";
  const picked = appState.pickedDoneTasks;
  const allPicked = doneTasks.length > 0 && doneTasks.every((task) => picked.includes(Number(task.id)));
  return `<details class="content-panel quest-done-panel collapsible-panel" id="quest-done-panel"${appState.questDoneOpen ? " open" : ""}>
    <summary class="collapsible-summary"><span class="section-copy"><span class="eyebrow">任务归档</span><strong class="section-copy-title">已完成任务（${doneTasks.length}）</strong></span><span aria-hidden="true" class="collapsible-caret">▾</span></summary>
    ${isAdmin ? `<div class="row-actions quest-done-tools"><label class="quest-pick"><input type="checkbox" id="quest-pick-all"${allPicked ? " checked" : ""}><span>全选</span></label><button class="button button-small button-outline-danger" data-action="batch-delete-tasks" type="button"${picked.length ? "" : " disabled"}>删除所选${picked.length ? `（${picked.length}）` : ""}</button></div>` : ""}
    <div class="quest-board quest-done-list">${doneTasks.map((task) => questCardMarkup(task, { done: true })).join("")}</div>
  </details>`;
}

function renderQuests() {
  const list = document.getElementById("quest-list");
  if (!list) return;
  const isAdmin = appState.data.user.role === "admin";
  const tasks = appState.data.tasks || [];
  if (!tasks.length) {
    list.innerHTML = isAdmin
      ? `<div class="content-panel empty-state">暂无悬赏任务，可以在上方发布第一个任务。</div>`
      : `<div class="content-panel empty-state">今天没有安排任务，好好休息一下吧。</div>`;
    return;
  }
  const isDone = (task) => isAdmin
    ? (task.assignments?.length > 0 && task.assignments.every((assignment) => assignment.status === "completed"))
    : task.my_assignment?.status === "completed";
  const doneTasks = tasks.filter(isDone);
  const activeTasks = tasks.filter((task) => !isDone(task));
  // 归档里被删掉的任务不再保留勾选
  appState.pickedDoneTasks = appState.pickedDoneTasks.filter((id) => doneTasks.some((task) => Number(task.id) === id));
  const emptyHint = !activeTasks.length
    ? `<div class="content-panel quest-all-done">${isAdmin ? "进行中的任务都已完成，可在下方归档里查看或删除。" : "今天的任务都完成了，真棒！"}</div>`
    : "";
  list.innerHTML = `${emptyHint}${activeTasks.map((task) => questCardMarkup(task)).join("")}${doneTasks.length ? questDoneSection(doneTasks) : ""}`;
}

// v0.11.0 每日提交审核额度：家长看到的是当前选中孩子的额度，孩子看到的是自己的。
function renderSubmitQuota() {
  const node = document.getElementById("quest-quota");
  if (!node) return;
  const quota = appState.data?.submit_quota;
  if (!quota) {
    node.classList.add("hidden");
    return;
  }
  node.classList.remove("hidden");
  const isAdmin = appState.data.user.role === "admin";
  const used = Number(quota.used || 0);
  const exhausted = !quota.unlimited && Number(quota.remaining ?? 0) <= 0;
  // 文案保持一行内可读（窄屏 360px 也不换行），细则放在账号弹窗的说明里
  if (quota.unlimited) {
    node.textContent = `今日提交审核：不限次数（已提交 ${used} 次）`;
  } else if (exhausted) {
    node.textContent = `${isAdmin ? "当前孩子" : "你"}今日提交审核已用完（${used} / ${quota.limit}），明天恢复`;
  } else {
    node.textContent = `${isAdmin ? "当前孩子今日提交" : "今日提交审核"}：还剩 ${quota.remaining} 次（已用 ${used} / ${quota.limit}）`;
  }
  node.classList.toggle("quest-quota-exhausted", exhausted);
}

function renderQuestFocus() {
  const focus = document.getElementById("child-quest-focus");
  if (!focus) return;
  const tasks = appState.data.tasks || [];
  // 优先展示今天真正能做的：史诗悬赏 → 今天触发的任务 → 其余（即将到来的）
  const task = tasks.find((item) => item.task_type === "epic" && item.active_today !== false)
    || tasks.find((item) => item.active_today !== false)
    || tasks[0];
  const title = document.getElementById("quest-focus-title");
  const description = document.getElementById("quest-focus-description");
  const reward = document.getElementById("quest-focus-reward");
  const exp = document.getElementById("quest-focus-exp");
  const action = document.getElementById("quest-focus-action");
  if (!task) {
    title.textContent = "等待新的悬赏任务";
    description.textContent = "管理员发布任务后，会在这里高亮展示。";
    reward.textContent = "0 积分";
    exp.textContent = "0 XP";
    action.classList.add("hidden");
    return;
  }
  title.textContent = task.title;
  description.textContent = task.description || "完成任务后提交，等待管理员验收。";
  const rewardCoins = Number(task.reward_coins);
  const baseReward = Number(task.base_reward_coins || rewardCoins);
  reward.textContent = `${rewardCoins.toLocaleString("zh-CN")} 积分${baseReward !== rewardCoins ? `（基础 ${baseReward.toLocaleString("zh-CN")}）` : ""}`;
  exp.textContent = `${Number(task.reward_exp).toLocaleString("zh-CN")} XP`;
  const assignment = task.my_assignment;
  const lockedToday = task.task_type === "repeat" && task.active_today === false;
  const actionState = lockedToday
    ? { action: "", id: "", label: task.next_date ? `下次 ${String(task.next_date).slice(5)} 开始` : "尚未开始" }
    : !assignment ? { action: "claim-task", id: task.id, label: "领取任务" } : assignment.status === "claimed" || assignment.status === "rejected" ? { action: "submit-task", id: assignment.id, label: assignment.status === "rejected" ? "重新提交" : "提交验收" } : { action: "", id: "", label: TASK_STATUS_TEXT[assignment.status] || assignment.status };
  action.textContent = actionState.label;
  action.dataset.action = actionState.action;
  action.dataset.id = actionState.id;
  action.classList.toggle("hidden", !actionState.action);
}

function renderAnnouncements() {
  const list = document.getElementById("announcement-list");
  if (!list) return;
  const isAdmin = appState.data.user.role === "admin";
  const announcements = appState.data.announcements || [];
  list.innerHTML = announcements.length ? announcements.map((item) => `<article class="announcement-card"><div class="announcement-card-head"><h3>${escapeHtml(item.title)}</h3>${isAdmin ? `<div class="row-actions"><button class="button button-small button-outline" data-action="edit-announcement" data-id="${item.id}" type="button">编辑</button><button class="button button-small button-outline-danger" data-action="delete-announcement" data-id="${item.id}" type="button">撤下</button></div>` : ""}</div><p>${escapeHtml(item.content)}</p><small>${item.audience === "children" ? "仅孩子账号可见" : "家庭全员可见"} · ${displayDateTime(item.updated_at || item.created_at)}</small></article>`).join("") : `<div class="empty-state">暂无通知</div>`;
  maybeShowAnnouncementPopup(announcements);
}

function announcementWasSeen(id) {
  try {
    return sessionStorage.getItem(`rewardhub-announcement-${id}`) === "1";
  } catch (_error) {
    return false;
  }
}

function markAnnouncementSeen(id) {
  try {
    sessionStorage.setItem(`rewardhub-announcement-${id}`, "1");
  } catch (_error) {
    // Private browsing may disable sessionStorage; the popup still works for this render.
  }
}

function closeAnnouncementPopup() {
  if (appState.announcementPopupTimer) {
    clearTimeout(appState.announcementPopupTimer);
    appState.announcementPopupTimer = null;
  }
  const popup = document.getElementById("announcement-popup");
  if (popup) {
    popup.classList.add("hidden");
    popup.setAttribute("aria-hidden", "true");
  }
}

function showAnnouncementPopup(item) {
  const popup = document.getElementById("announcement-popup");
  const title = document.getElementById("announcement-popup-title");
  const content = document.getElementById("announcement-popup-content");
  const countdown = document.getElementById("announcement-popup-countdown");
  if (!popup || !title || !content || !countdown) return;
  closeAnnouncementPopup();
  title.textContent = item.title || "家庭通知";
  content.textContent = item.content || "";
  countdown.textContent = "3 秒后自动关闭";
  popup.classList.remove("hidden");
  popup.setAttribute("aria-hidden", "false");
  appState.announcementPopupTimer = window.setTimeout(closeAnnouncementPopup, 3000);
}

function maybeShowAnnouncementPopup(announcements) {
  if (appState.data?.user?.role !== "child") {
    closeAnnouncementPopup();
    return;
  }
  const popup = document.getElementById("announcement-popup");
  if (popup && !popup.classList.contains("hidden")) return;
  const next = announcements.find((item) => !announcementWasSeen(item.id));
  if (!next) return;
  markAnnouncementSeen(next.id);
  showAnnouncementPopup(next);
}

function resetAnnouncementEditor() {
  const form = document.getElementById("announcement-form");
  if (!form) return;
  appState.announcementEditId = null;
  form.reset();
  form.elements.announcement_id.value = "";
  form.querySelector("button[type='submit']").textContent = "发布通知";
  document.getElementById("cancel-announcement-edit")?.classList.add("hidden");
}

function openAnnouncementEdit(id) {
  const announcement = (appState.data.announcements || []).find((item) => Number(item.id) === Number(id));
  const form = document.getElementById("announcement-form");
  if (!announcement || !form) return;
  appState.announcementEditId = Number(id);
  appState.announcementFormOpen = true;
  form.elements.announcement_id.value = announcement.id;
  form.elements.title.value = announcement.title;
  form.elements.content.value = announcement.content;
  form.elements.audience.value = announcement.audience;
  form.querySelector("button[type='submit']").textContent = "保存通知";
  document.getElementById("cancel-announcement-edit")?.classList.remove("hidden");
  syncAnnouncementEditor();
  form.elements.title.focus();
}

async function saveAnnouncement(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    title: form.elements.title.value.trim(),
    content: form.elements.content.value.trim(),
    audience: form.elements.audience.value,
  };
  if (!payload.title || !payload.content) {
    showToast("请填写通告标题和内容");
    return;
  }
  try {
    const url = appState.announcementEditId ? `/api/announcements/${appState.announcementEditId}` : "/api/announcements";
    appState.data = await api(url, {
      method: appState.announcementEditId ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    resetAnnouncementEditor();
    appState.announcementFormOpen = false;
    render();
    showToast("通告已保存");
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteAnnouncement(id) {
  if (!await requestConfirm("撤下后孩子将不再看到这条通告，确定继续吗？", { title: "撤下通告", confirmLabel: "确认撤下" })) return;
  try {
    appState.data = await api(`/api/announcements/${id}`, { method: "DELETE" });
    if (appState.announcementEditId === Number(id)) resetAnnouncementEditor();
    render();
    showToast("通告已撤下");
  } catch (error) {
    showToast(error.message);
  }
}

function renderAchievements() {
  const list = document.getElementById("achievement-list");
  if (!list) return;
  const achievements = appState.data.achievements || [];
  list.innerHTML = achievements.length ? achievements.map((achievement) => `<article class="achievement-card${achievement.unlocked ? "" : " locked"}"><div class="achievement-medal"><img src="${illustrationSource(achievement.icon, "reward")}" alt=""></div><strong>${escapeHtml(achievement.title)}</strong><p>${escapeHtml(achievement.description)}</p><small>${achievement.unlocked ? `已解锁 · ${displayDateTime(achievement.unlocked_at)}` : "未解锁"}</small></article>`).join("") : `<div class="content-panel empty-state">创建孩子账号后即可开始收集成就。</div>`;
}

// 待办口径（v0.10.1）：积分申请 + 任务验收，两处表格共用
function pendingTotal(item) {
  return Number(item?.pending_count || 0) + Number(item?.task_pending_count || 0);
}

// v0.13.2：账号管理页改为「一账号一折叠卡片」——摘要一行（头像/名称/积分/待审核），明细展开看。
function accountCardMarkup(account, currentId) {
  const isChild = account.role === "child";
  const limit = Number(account.daily_submit_limit || 0);
  const used = Number(account.today_submit_count || 0);
  const quotaText = isChild ? (limit ? `${used} / ${limit}` : `${used} / 不限`) : "—";
  const quotaOver = isChild && limit > 0 && used >= limit;
  const pending = pendingTotal(account);
  const roleText = isChild ? "孩子账号" : "管理账号";
  const open = appState.openAccounts[String(account.id)] ? " open" : "";
  const deleteButton = Number(account.id) === currentId ? "" : `<button class="button button-small button-outline-danger" data-action="delete-account" data-id="${account.id}" type="button">删除</button>`;
  return `<details class="account-card" data-account-id="${account.id}"${open}><summary class="account-card-summary"><span class="table-person">${avatarImage(account.avatar, "avatar avatar-table", account.display_name)}<span class="account-card-name"><strong>${escapeHtml(account.display_name)}</strong><small>${escapeHtml(account.username)} · ${roleText}</small></span></span><span class="account-card-side"><span class="account-card-points"><strong>${Number(account.total_points).toLocaleString("zh-CN")}</strong><small>${moneyText(account.total_points)}</small></span><span class="pending-badge" title="待审核事项">${pending}</span><span aria-hidden="true" class="collapsible-caret">▾</span></span></summary><div class="account-card-body"><dl class="account-facts"><div><dt>登录账号</dt><dd>${escapeHtml(account.username)}</dd></div><div><dt>账号类型</dt><dd>${roleText}</dd></div><div><dt>今日变化</dt><dd class="${Number(account.today_net) >= 0 ? "income" : "expense"}">${signed(account.today_net)}</dd></div><div><dt>待审核</dt><dd>${pending} 项</dd></div><div><dt>今日提交</dt><dd class="${quotaOver ? "quota-over" : ""}">${quotaText}</dd></div><div><dt>折合金额</dt><dd>${moneyText(account.total_points)}</dd></div></dl><div class="row-actions"><button class="button button-small button-outline" data-action="edit-account" data-id="${account.id}" type="button">编辑</button>${deleteButton}</div></div></details>`;
}

function renderAccounts() {
  const summaryBody = document.getElementById("account-summary-body");
  const logBody = document.getElementById("account-log-body");
  if (!summaryBody || !logBody || appState.data.user.role !== "admin") return;
  const currentId = Number(appState.data.user.id);
  const overview = appState.data.account_overview || [];
  summaryBody.innerHTML = overview.length
    ? overview.map((account) => accountCardMarkup(account, currentId)).join("")
    : `<div class="empty-state">暂无账号</div>`;
  const toggleAll = document.getElementById("toggle-account-cards");
  if (toggleAll) {
    const cards = [...summaryBody.querySelectorAll("details.account-card")];
    const anyClosed = cards.some((card) => !card.open);
    toggleAll.textContent = anyClosed ? "全部展开" : "全部收起";
    toggleAll.setAttribute("aria-expanded", anyClosed ? "false" : "true");
  }
  const actionText = { create_child: "新增孩子", register_child: "孩子自助注册", create_admin: "新增管理", update_child: "修改孩子资料", update_admin: "修改管理资料", delete_child: "删除孩子", delete_admin: "删除管理", change_password: "孩子修改密码" };
  logBody.innerHTML = (appState.data.account_logs || []).length ? appState.data.account_logs.map((log) => `<tr><td>${displayDateTime(log.created_at)}</td><td><div class="table-person">${avatarImage(log.actor_avatar, "avatar avatar-table", log.actor_name)}<strong>${escapeHtml(log.actor_name)}</strong></div></td><td><span class="log-action ${log.target_role === "admin" ? "admin" : "child"}">${actionText[log.action] || escapeHtml(log.action)}</span></td><td><div class="table-person">${avatarImage(log.target_avatar, "avatar avatar-table", log.target_name)}<div><strong>${escapeHtml(log.target_name)}</strong><small>${escapeHtml(log.target_username)}</small></div></div></td><td>${log.target_role === "admin" ? "管理账号" : "孩子账号"}</td></tr>`).join("") : `<tr><td colspan="5"><div class="empty-state">暂无账号变更记录</div></td></tr>`;
}

function renderWeekGrid(container, titleId) {
  if (!container) return;
  const monday = new Date();
  const day = monday.getDay() || 7;
  monday.setDate(monday.getDate() - day + 1);
  let total = 0;
  container.innerHTML = dayNames.map((dayName, index) => {
    const current = new Date(monday);
    current.setDate(monday.getDate() + index);
    const date = localDate(current);
    const amount = dayTotal(date);
    total += amount;
    return `<button class="day-item${date === localDate() ? " today" : ""}${date === appState.selectedDate ? " selected" : ""}" data-select-date="${date}" type="button"><span>${dayName}</span><strong>${signed(amount)}</strong></button>`;
  }).join("");
  const title = document.getElementById(titleId);
  if (title) title.textContent = `本周积分（${signed(total)}）`;
}

function renderRecords() {
  const weekGrid = document.getElementById("records-week-grid");
  if (!weekGrid) return;
  renderWeekGrid(weekGrid, "records-week-title");
  document.getElementById("selected-day-title").textContent = `${appState.selectedDate} 每日记录`;
  const records = recordsFor(appState.selectedDate);
  document.getElementById("day-records").innerHTML = records.length ? records.map((record) => `<div class="record-row"><div><strong>${escapeHtml(record.title)}</strong><span>${escapeHtml(record.time)}</span></div><strong class="record-amount ${record.type}">${signed(record.amount)} 积分</strong>${appState.data.user.role === "admin" ? `<button class="button button-small button-outline-danger" data-action="undo" data-id="${record.id}" type="button">撤销</button>` : ""}</div>`).join("") : `<div class="empty-state">该日期暂无积分记录</div>`;
  renderHistory();
}

function renderHistory() {
  const year = appState.historyYear;
  const month = appState.historyMonth;
  document.getElementById("history-month-label").textContent = `${year}年${month + 1}月`;
  const first = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startPadding = (first.getDay() || 7) - 1;
  const daily = new Map();
  (appState.data.records || []).forEach((record) => daily.set(record.date, (daily.get(record.date) || 0) + Number(record.amount)));
  let cells = Array.from({ length: startPadding }, () => `<div class="month-day empty"></div>`).join("");
  for (let day = 1; day <= daysInMonth; day += 1) {
    const value = daily.get(`${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`) || 0;
    cells += `<div class="month-day${day === new Date().getDate() && month === new Date().getMonth() && year === new Date().getFullYear() ? " today" : ""}"><span>${day}</span><strong>${value ? signed(value) : ""}</strong></div>`;
  }
  document.getElementById("history-calendar").innerHTML = `<div class="month-calendar"><div class="month-weekdays">${dayNames.map((name) => `<span>${name.slice(1)}</span>`).join("")}</div><div class="month-days">${cells}</div></div>`;
}

function openEditor(kind, id = null) {
  appState.editorKind = kind;
  appState.editorId = id;
  const item = id ? findItem(kind, id) : null;
  const itemIconKnown = Boolean(item?.icon && (PROJECT_ICONS.some(([file]) => file === item.icon) || BUILTIN_ICON_MAP.has(item.icon)));
  appState.selectedIcon = itemIconKnown ? item.icon : DEFAULT_ITEM_ICONS[kind];
  document.getElementById("modal-title").textContent = `${item ? "编辑" : "新增"}${kind === "earn" ? "加积分项目" : kind === "reward" ? "兑换奖励" : "扣积分项目"}`;
  document.getElementById("editor-name").value = item?.name || "";
  document.getElementById("editor-points").value = item ? Math.abs(Number(item.points)) : "";
  renderIconPicker();
  showModal("editor-form");
}

function renderIconPicker() {
  const container = document.getElementById("editor-icon-groups");
  if (!container) return;
  renderIconGroups(container, document.getElementById("icon-search")?.value || "", appState.selectedIcon, "data-project-icon");
  document.getElementById("editor-icon").value = appState.selectedIcon || "";
}

function renderIconGroups(container, query = "", selected = "", dataAttribute = "data-project-icon") {
  if (!container) return;
  const normalized = String(query).trim().toLowerCase();
  const fileGroup = { name: "基础图标", items: PROJECT_ICONS.map(([file, label]) => [file, label, null]) };
  const groups = [fileGroup, ...BUILTIN_ICON_GROUPS.map((group) => ({ name: group.name, items: group.items.map(([key, label, emoji]) => [`emoji:${key}`, label, emoji]) }))];
  container.innerHTML = groups.map((group) => {
    const items = group.items.filter(([token, label]) => !normalized || `${token} ${label} ${group.name}`.toLowerCase().includes(normalized));
    if (!items.length) return "";
    const open = normalized ? " open" : "";
    const choices = items.map(([token, label, emoji]) => `<button class="icon-choice${token === selected ? " selected" : ""}" ${dataAttribute}="${token}" type="button" title="${escapeHtml(label)}" aria-label="${escapeHtml(label)}">${emoji ? `<span class="icon-emoji">${emoji}</span>` : `<img src="/static/illustrations/${token}" alt="">`}<span>${escapeHtml(label)}</span></button>`).join("");
    return `<details class="icon-group"${open}><summary>${escapeHtml(group.name)} · ${items.length}</summary><div class="item-icon-picker">${choices}</div></details>`;
  }).join("") || `<div class="empty-state">没有匹配的内置图标</div>`;
}

function renderQuestIconPicker() {
  const container = document.getElementById("quest-icon-groups");
  if (!container) return;
  renderIconGroups(container, document.getElementById("quest-icon-search")?.value || "", document.getElementById("quest-icon")?.value || "", "data-task-icon");
}

// ---- 重复任务表单（v0.9.0）----
const WEEKDAY_LABELS = { 1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日" };
let repeatFormApi = { sync: () => {}, setDays: () => {} };

function setupRepeatForm() {
  const panel = document.getElementById("repeat-panel");
  const typeSelect = document.getElementById("quest-type");
  const freqSelect = document.getElementById("repeat-freq");
  const monthField = document.getElementById("repeat-month-week-field");
  const monthSelect = document.getElementById("repeat-month-week");
  const weekdaysField = document.getElementById("repeat-weekdays-field");
  const hidden = document.getElementById("repeat-days-value");
  const hint = document.getElementById("repeat-hint");
  const chips = [...document.querySelectorAll("#weekday-chips .weekday-chip")];
  if (!panel || !typeSelect || !freqSelect || !hidden) return;

  const selectedDays = () => chips
    .filter((chip) => chip.classList.contains("on"))
    .map((chip) => Number(chip.dataset.weekday))
    .sort((a, b) => a - b);
  const setDays = (days) => chips.forEach((chip) => chip.classList.toggle("on", days.includes(Number(chip.dataset.weekday))));

  function sync() {
    const isRepeat = typeSelect.value === "repeat";
    const days = selectedDays();
    // 无论面板是否可见都同步一次，避免切换类型时残留上一次的选择
    hidden.value = days.join(",");
    panel.classList.toggle("hidden", !isRepeat);
    if (!isRepeat) return;
    const freq = freqSelect.value;
    weekdaysField.classList.toggle("hidden", freq === "daily");
    monthField.classList.toggle("hidden", freq !== "monthly");
    if (freq === "daily") {
      hint.textContent = "每天都会自动出现，不需要选择星期。";
      return;
    }
    if (!days.length) {
      hint.textContent = "请至少选择一个星期，否则任务不会触发。";
      return;
    }
    const names = days.map((day) => WEEKDAY_LABELS[day]).join("、");
    hint.textContent = freq === "weekly"
      ? `每周${names}自动出现，孩子打开任务页就能看到。`
      : `每月第 ${monthSelect.value === "5" ? "最后一个" : monthSelect.value} 个周${names}自动出现。`;
  }

  chips.forEach((chip) => chip.addEventListener("click", () => {
    chip.classList.toggle("on");
    sync();
  }));
  document.querySelectorAll("#repeat-panel [data-repeat-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = button.dataset.repeatPreset;
      if (preset === "weekdays") setDays([1, 2, 3, 4, 5]);
      else if (preset === "weekend") setDays([6, 7]);
      else if (preset === "all") setDays([1, 2, 3, 4, 5, 6, 7]);
      else setDays([]);
      sync();
    });
  });
  typeSelect.addEventListener("change", () => {
    if (typeSelect.value === "repeat" && freqSelect.value !== "daily" && !selectedDays().length) setDays([1, 2, 3, 4, 5]);
    sync();
  });
  freqSelect.addEventListener("change", () => {
    if (freqSelect.value !== "daily" && !selectedDays().length) setDays([1, 2, 3, 4, 5]);
    sync();
  });
  monthSelect.addEventListener("change", sync);

  repeatFormApi = { sync, setDays };
  sync();
}

function openManual() {
  const form = document.getElementById("manual-form");
  form.reset();
  form.elements.date.value = appState.selectedDate || localDate();
  showModal("manual-form");
}

function fillAvatarOptions(role, selected = "") {
  const options = role === "admin" ? ["adult-male", "adult-female"] : ["boy", "girl"];
  document.getElementById("account-avatar").innerHTML = options.map((value) => `<option value="${value}" ${value === selected ? "selected" : ""}>${AVATARS[value].label}</option>`).join("");
}

function openAccount() {
  appState.accountEditId = null;
  const form = document.getElementById("account-form");
  form.reset();
  document.getElementById("account-modal-title").textContent = "新增账号";
  document.getElementById("account-username-field").classList.remove("hidden");
  document.getElementById("account-role-field").classList.remove("hidden");
  document.getElementById("account-limit-field").classList.remove("hidden");
  form.elements.username.required = true;
  form.elements.password.required = true;
  fillAvatarOptions("child", "boy");
  showModal("account-form");
}

function openEditAccount(id) {
  const account = (appState.data.account_overview || []).find((item) => Number(item.id) === Number(id));
  if (!account) return;
  appState.accountEditId = Number(id);
  const form = document.getElementById("account-form");
  form.reset();
  document.getElementById("account-modal-title").textContent = `编辑 ${account.display_name}`;
  document.getElementById("account-username-field").classList.add("hidden");
  document.getElementById("account-role-field").classList.add("hidden");
  form.elements.username.required = false;
  form.elements.display_name.value = account.display_name;
  form.elements.password.required = false;
  document.getElementById("account-limit-field").classList.toggle("hidden", account.role !== "child");
  form.elements.daily_submit_limit.value = account.daily_submit_limit ?? DEFAULT_SUBMIT_LIMIT;
  fillAvatarOptions(account.role, account.avatar);
  showModal("account-form");
}

function openSelfPassword() {
  const form = document.getElementById("self-password-form");
  form.reset();
  showModal("self-password-form");
}

function showModal(formId) {
  ["editor-form", "manual-form", "account-form", "self-password-form", "confirm-modal"].forEach((id) => document.getElementById(id).classList.toggle("hidden", id !== formId));
  document.getElementById("modal-backdrop").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("modal-backdrop")?.classList.add("hidden");
  if (confirmResolver) {
    const resolve = confirmResolver;
    confirmResolver = null;
    resolve(false);
  }
}

function requestConfirm(message, options = {}) {
  return new Promise((resolve) => {
    if (confirmResolver) confirmResolver(false);
    confirmResolver = resolve;
    document.getElementById("confirm-title").textContent = options.title || "请确认操作";
    document.getElementById("confirm-message").textContent = message;
    const submit = document.getElementById("confirm-submit");
    submit.textContent = options.confirmLabel || "确认";
    submit.classList.toggle("button-danger", options.danger !== false);
    submit.classList.toggle("button-primary", options.danger === false);
    showModal("confirm-modal");
    requestAnimationFrame(() => document.getElementById("confirm-cancel")?.focus());
  });
}

function settleConfirm(confirmed) {
  const resolve = confirmResolver;
  confirmResolver = null;
  document.getElementById("modal-backdrop")?.classList.add("hidden");
  resolve?.(confirmed);
}

function findItem(kind, id) {
  const source = kind === "earn" ? appState.data.earn_items : kind === "exchange" || kind === "reward" ? appState.data.rewards : appState.data.deduct_items;
  return source.find((item) => Number(item.id) === Number(id));
}

async function saveAccount(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = { display_name: form.elements.display_name.value.trim(), password: form.elements.password.value, avatar: form.elements.avatar.value };
  const limitField = document.getElementById("account-limit-field");
  if (!limitField.classList.contains("hidden")) {
    const raw = String(form.elements.daily_submit_limit.value || "").trim();
    const limit = raw === "" ? DEFAULT_SUBMIT_LIMIT : Number(raw);
    if (!Number.isInteger(limit) || limit < 0 || limit > MAX_SUBMIT_LIMIT) {
      showToast(`每日提交上限必须是 0 到 ${MAX_SUBMIT_LIMIT} 的整数（0 表示不限制）`);
      return;
    }
    payload.daily_submit_limit = limit;
  }
  try {
    if (appState.accountEditId) {
      await api(`/api/accounts/${appState.accountEditId}`, { method: "PUT", body: JSON.stringify(payload) });
      showToast("账号资料已更新");
    } else {
      payload.username = form.elements.username.value.trim();
      payload.role = form.elements.role.value;
      await api("/api/accounts", { method: "POST", body: JSON.stringify(payload) });
      showToast("账号已创建");
    }
    closeModal();
    await loadState();
    navigate("accounts");
  } catch (error) { showToast(error.message); }
}

async function saveSelfPassword(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (form.elements.password.value !== form.elements.password_confirm.value) {
    showToast("两次输入的新密码不一致");
    return;
  }
  try {
    await api("/api/auth/password", {
      method: "PUT",
      body: JSON.stringify({
        current_password: form.elements.current_password.value,
        password: form.elements.password.value,
        password_confirm: form.elements.password_confirm.value,
      }),
    });
    closeModal();
    showToast("密码已修改");
  } catch (error) {
    showToast(error.message);
  }
}

function updateCashExchangePreview() {
  const input = document.querySelector("#cash-exchange-form input[name='points']");
  const preview = document.getElementById("cash-exchange-preview");
  if (!input || !preview) return;
  const basePoints = Math.max(0, Number(input.value) || 0);
  const chargedPoints = basePoints > 0 ? effectiveItemPoints(basePoints, "exchange", "child") : 0;
  const savedPoints = Math.max(0, basePoints - chargedPoints);
  const note = savedPoints > 0
    ? `实扣 ${chargedPoints.toLocaleString("zh-CN")} 积分（省 ${savedPoints.toLocaleString("zh-CN")}）`
    : `实扣 ${chargedPoints.toLocaleString("zh-CN")} 积分`;
  preview.textContent = `到账 ${moneyText(basePoints)} · ${note}`;
}

function updateCashExchangeDiscount() {
  const note = document.getElementById("cash-exchange-discount");
  if (!note) return;
  const discount = Number(appState.data?.gamification?.exchange_discount_percent || 0);
  note.textContent = discount > 0
    ? `当前等级现金兑换省 ${discount}% · 实际扣除积分按等级优惠计算`
    : "当前等级暂无现金兑换折扣 · 实际扣除积分按基础比例计算";
}

async function saveCashExchange(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const points = Number(form.elements.points.value);
  if (!Number.isInteger(points) || points <= 0) {
    showToast("请输入有效兑换积分");
    return;
  }
  try {
    const result = await api("/api/transactions", { method: "POST", body: JSON.stringify({ kind: "cash_exchange", points }) });
    appState.data = result;
    form.reset();
    updateCashExchangePreview();
    render();
    showToast("现金兑换申请已提交，等待管理账号审核");
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteAccount(id) {
  if (!await requestConfirm("删除账号会同时删除积分和记录，确定继续吗？", { title: "删除账号", confirmLabel: "删除账号" })) return;
  try { await api(`/api/accounts/${id}`, { method: "DELETE" }); await loadState(); navigate("accounts"); showToast("账号已删除"); } catch (error) { showToast(error.message); }
}

async function reviewRequest(action, id) {
  const message = action === "approve" ? "通过后积分会立即计入孩子余额，确定吗？" : "确定拒绝这条申请吗？";
  if (!await requestConfirm(message, { title: action === "approve" ? "通过申请" : "拒绝申请", confirmLabel: action === "approve" ? "通过" : "拒绝", danger: action !== "approve" })) return;
  try {
    appState.data = await api(`/api/requests/${id}/${action}`, { method: "POST", body: JSON.stringify(action === "reject" ? { reason: "管理账号拒绝了这条申请" } : {}) });
    if (appState.data.user.role === "admin") appState.accounts = (await api("/api/accounts")).accounts;
    render();
    showToast(action === "approve" ? "申请已通过" : "申请已拒绝");
  } catch (error) { showToast(error.message); }
}

async function handleOperation(kind, id = null, form = null) {
  const item = id ? findItem(kind, id) : null;
  const name = form ? form.elements.name.value.trim() : item?.name || "";
  const points = form ? Number(form.elements.points.value) : Math.abs(Number(item?.points));
  if (!Number.isInteger(points) || points <= 0) throw new Error("请输入有效积分");
  const payload = { kind, name, points };
  if (item) payload.item_id = item.id;
  if (kind === "exchange" && item) {
    delete payload.item_id;
    payload.reward_id = item.id;
  }
  const result = await api("/api/transactions", { method: "POST", body: JSON.stringify(payload) });
  appState.data = result;
  if (form) form.reset();
  render();
  showToast(result.request_submitted ? "申请已提交，等待管理账号审核" : kind === "earn" ? "已给孩子加积分" : kind === "exchange" ? "兑换已提交，等待管理账号审核" : "已扣取孩子积分");
}

async function saveEditor(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = { name: form.elements.name.value.trim(), points: Number(form.elements.points.value), icon: appState.selectedIcon || form.elements.icon.value };
  if (!payload.name || !Number.isInteger(payload.points) || payload.points <= 0) { showToast("请填写有效项目和积分"); return; }
  try {
    const url = appState.editorId ? `/api/items/${appState.editorKind}/${appState.editorId}` : `/api/items/${appState.editorKind}`;
    await api(url, { method: appState.editorId ? "PUT" : "POST", body: JSON.stringify(payload) });
    closeModal();
    await loadState();
    showToast(appState.editorId ? "项目已更新" : "项目已添加");
  } catch (error) { showToast(error.message); }
}

async function saveCurrencySettings(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const pointsPerYuan = Number(form.elements.points_per_yuan.value);
  if (!Number.isInteger(pointsPerYuan) || pointsPerYuan < 1 || pointsPerYuan > 1000000) {
    showToast("换算比例必须是 1 到 1000000 的整数");
    return;
  }
  try {
    appState.data = await api("/api/settings", { method: "PUT", body: JSON.stringify({ points_per_yuan: pointsPerYuan }) });
    render();
    showToast("换钱比例已保存");
  } catch (error) {
    showToast(error.message);
  }
}

async function saveAdventureLevel(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const mode = form.elements.mode.value;
  const level = form.elements.level.value.trim();
  if (mode === "manual" && (!Number.isInteger(Number(level)) || Number(level) < 1 || Number(level) > 99)) {
    showToast("冒险等级必须是 1 到 99 的整数");
    return;
  }
  try {
    appState.data = await api("/api/settings", { method: "PUT", body: JSON.stringify({ adventure_level: mode === "auto" ? "auto" : Number(level) }) });
    render();
    showToast(mode === "auto" ? "已恢复自动计算等级" : "冒险等级已设置为 " + level);
  } catch (error) {
    showToast(error.message);
  }
}

function resetQuestForm() {
  const form = document.getElementById("quest-form");
  if (!form) return;
  form.reset();
  form.elements.reward_coins.value = 20;
  form.elements.reward_exp.value = 10;
  repeatFormApi.setDays([]);
  repeatFormApi.sync();
  syncTaskFormMode();
}

function syncTaskFormMode() {
  const editing = Boolean(appState.taskEditId);
  const submit = document.getElementById("quest-submit");
  if (submit) submit.textContent = editing ? "保存修改" : "发布任务";
  const cancel = document.getElementById("quest-cancel-edit");
  if (cancel) cancel.classList.toggle("hidden", !editing);
  const heading = document.getElementById("quest-form-title");
  if (heading) heading.textContent = editing ? "编辑任务" : "发布新悬赏";
}

function startTaskEdit(id) {
  const task = (appState.data.tasks || []).find((item) => Number(item.id) === Number(id));
  if (!task) return;
  if (task.edit_locked) { showToast("该任务已有审核通过的提交，不能再编辑"); return; }
  const form = document.getElementById("quest-form");
  appState.taskEditId = Number(id);
  form.elements.title.value = task.title || "";
  form.elements.description.value = task.description || "";
  form.elements.category.value = task.category || "生活";
  form.elements.task_type.value = task.task_type || "daily";
  form.elements.difficulty.value = task.difficulty || "normal";
  form.elements.reward_coins.value = Number(task.base_reward_coins || task.reward_coins) || 20;
  form.elements.reward_exp.value = Number(task.reward_exp) || 10;
  form.elements.due_date.value = task.due_date || "";
  if (task.icon && [...form.elements.icon.options].some((option) => option.value === task.icon)) {
    form.elements.icon.value = task.icon;
  }
  form.elements.repeat_freq.value = task.repeat_freq || "weekly";
  form.elements.repeat_month_week.value = String(task.repeat_month_week || 1);
  form.elements.repeat_start.value = task.repeat_start || "";
  form.elements.repeat_end.value = task.repeat_end || "";
  repeatFormApi.setDays(Array.isArray(task.repeat_days) ? task.repeat_days : []);
  repeatFormApi.sync();
  syncTaskFormMode();
  document.getElementById("quest-form-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
  showToast(`正在编辑「${task.title}」`);
}

async function deleteTask(id) {
  const task = (appState.data.tasks || []).find((item) => Number(item.id) === Number(id));
  if (!task) return;
  const inFlight = (task.assignments || []).filter((assignment) => ["claimed", "submitted"].includes(assignment.status)).length;
  const extra = inFlight ? `已有 ${inFlight} 条领取/提交记录会一并归档。` : "";
  if (!await requestConfirm(`删除「${task.title}」后孩子将不再看到这个任务。${extra}确定继续吗？`, { title: "删除任务", confirmLabel: "删除任务" })) return;
  try {
    await api(`/api/tasks/${id}`, { method: "DELETE" });
    if (Number(appState.taskEditId) === Number(id)) {
      appState.taskEditId = null;
      resetQuestForm();
    }
    await loadState();
    navigate("quests");
    showToast("任务已删除");
  } catch (error) { showToast(error.message); }
}

// v0.13.5：批量删除归档里勾选的已完成任务（一次确认，逐个调删除接口，中途失败即停）
async function batchDeleteDoneTasks() {
  const ids = [...appState.pickedDoneTasks];
  if (!ids.length) return;
  const tasks = appState.data.tasks || [];
  const names = ids.map((id) => (tasks.find((task) => Number(task.id) === id) || {}).title || `#${id}`);
  const label = names.length <= 3 ? `（${names.map((name) => `「${name}」`).join(" ")}）` : "";
  if (!await requestConfirm(`确定删除选中的 ${ids.length} 个已完成任务吗？${label}删除后孩子将不再看到这些任务。`, { title: "批量删除任务", confirmLabel: "删除" })) return;
  let removed = 0;
  for (const id of ids) {
    try {
      await api(`/api/tasks/${id}`, { method: "DELETE" });
      removed += 1;
      if (Number(appState.taskEditId) === Number(id)) { appState.taskEditId = null; resetQuestForm(); }
    } catch (error) {
      showToast(error.message);
      break;
    }
  }
  appState.pickedDoneTasks = [];
  await loadState();
  navigate("quests");
  showToast(removed === ids.length ? `已删除 ${removed} 个任务` : `已删除 ${removed} / ${ids.length} 个任务`);
}

async function saveTask(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const editingId = appState.taskEditId;
  const payload = {
    title: form.elements.title.value.trim(),
    description: form.elements.description.value.trim(),
    category: form.elements.category.value,
    task_type: form.elements.task_type.value,
    difficulty: form.elements.difficulty.value,
    reward_coins: Number(form.elements.reward_coins.value),
    reward_exp: Number(form.elements.reward_exp.value),
    due_date: form.elements.due_date.value,
    icon: form.elements.icon.value,
  };
  if (!payload.title || !Number.isInteger(payload.reward_coins) || payload.reward_coins <= 0 || !Number.isInteger(payload.reward_exp) || payload.reward_exp <= 0) {
    showToast("请填写任务标题、积分和经验奖励");
    return;
  }
  if (payload.task_type === "repeat") {
    payload.repeat_freq = form.elements.repeat_freq.value;
    payload.repeat_days = form.elements.repeat_days.value;
    payload.repeat_month_week = Number(form.elements.repeat_month_week.value);
    payload.repeat_start = form.elements.repeat_start.value;
    payload.repeat_end = form.elements.repeat_end.value;
    if (payload.repeat_start && payload.repeat_end && payload.repeat_end < payload.repeat_start) {
      showToast("生效结束日期不能早于开始日期");
      return;
    }
    if (payload.repeat_freq !== "daily" && !payload.repeat_days) {
      showToast("请至少选择一个触发星期");
      return;
    }
  }
  try {
    if (editingId) {
      appState.data = await api(`/api/tasks/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      appState.taskEditId = null;
      resetQuestForm();
      render();
      showToast("任务已更新");
      return;
    }
    const result = await api("/api/tasks", { method: "POST", body: JSON.stringify(payload) });
    appState.data = result.state;
    resetQuestForm();
    render();
    showToast(payload.task_type === "repeat" ? "重复任务已发布，到点会自动出现" : "悬赏任务已发布");
  } catch (error) { showToast(error.message); }
}

async function handleTaskAction(action, id) {
  const labels = { claim: "领取任务", submit: "提交验收", approve: "通过验收", reject: "要求重做" };
  if (["approve", "reject"].includes(action) && !await requestConfirm(action === "approve" ? "通过后会发放积分和经验，确定吗？" : "要求孩子重新完成这个任务吗？", { title: labels[action], confirmLabel: labels[action], danger: action === "reject" })) return;
  const endpoint = action === "claim" ? `/api/tasks/${id}/claim` : `/api/task-assignments/${id}/${action}`;
  try {
    const result = await api(endpoint, { method: "POST", body: JSON.stringify(action === "reject" ? { reason: "请按任务说明完成后重新提交" } : {}) });
    appState.data = result.state || result;
    render();
    showToast(action === "claim" ? "已领取任务" : action === "submit" ? "已提交验收" : action === "approve" ? "任务已完成，积分和经验已发放" : "已退回任务");
  } catch (error) {
    showToast(error.message);
    // 撞上每日提交额度（429）时把额度提示条刷新到最新
    if (error.status === 429) await syncState({ force: true });
  }
}

async function saveManual(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const points = Number(form.elements.points.value);
  if (!Number.isInteger(points) || points === 0) { showToast("积分数值不能为 0"); return; }
  try {
    appState.data = await api("/api/transactions", { method: "POST", body: JSON.stringify({ kind: "manual", name: form.elements.name.value.trim(), points, date: form.elements.date.value }) });
    appState.selectedDate = form.elements.date.value;
    closeModal();
    render();
    showToast("积分已补录");
  } catch (error) { showToast(error.message); }
}

async function deleteItem(kind, id) {
  if (!await requestConfirm("确定删除这个项目吗？", { title: "删除项目", confirmLabel: "删除项目" })) return;
  try { await api(`/api/items/${kind}/${id}`, { method: "DELETE" }); await loadState(); showToast("项目已删除"); } catch (error) { showToast(error.message); }
}

async function undoRecord(id) {
  if (!await requestConfirm("撤销后积分余额会回滚，确定继续吗？", { title: "撤销积分记录", confirmLabel: "确认撤销" })) return;
  try { appState.data = await api(`/api/transactions/${id}/undo`, { method: "POST" }); render(); showToast("记录已撤销"); } catch (error) { showToast(error.message); }
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2600);
}

document.addEventListener("click", async (event) => {
  const pageTarget = event.target.closest("[data-page-target]");
  if (pageTarget) { navigate(pageTarget.dataset.pageTarget); return; }
  const settingsTabTarget = event.target.closest("[data-settings-tab]");
  if (settingsTabTarget) { appState.settingsTab = settingsTabTarget.dataset.settingsTab; syncSettingsTabs(); return; }
  const itemTabTarget = event.target.closest("[data-item-tab]");
  if (itemTabTarget) { appState.itemTab = itemTabTarget.dataset.itemTab; syncItemTabs(); return; }
  const dateTarget = event.target.closest("[data-select-date]");
  if (dateTarget) { appState.selectedDate = dateTarget.dataset.selectDate; navigate("records"); return; }
  const iconTarget = event.target.closest("[data-project-icon]");
  if (iconTarget) {
    appState.selectedIcon = iconTarget.dataset.projectIcon;
    renderIconPicker();
    return;
  }
  const taskIconTarget = event.target.closest("[data-task-icon]");
  if (taskIconTarget) {
    const select = document.getElementById("quest-icon");
    if (select) {
      const token = taskIconTarget.dataset.taskIcon;
      if (![...select.options].some((option) => option.value === token)) {
        const label = taskIconTarget.getAttribute("aria-label") || "内置图标";
        select.add(new Option(label, token));
      }
      select.value = token;
      renderQuestIconPicker();
    }
    return;
  }
  const editorTarget = event.target.closest("[data-open-editor]");
  if (editorTarget) {
    // v0.13.0：三个项目面板改成 Tab 后，点「新增」要先切到对应 Tab，否则表单藏在别的分区里
    const kind = editorTarget.dataset.openEditor;
    if (["earn", "deduct", "reward"].includes(kind)) { appState.itemTab = kind; syncItemTabs(); }
    // 折叠面板时点「新增」要自动展开，否则保存后新条目藏在收起区里看不见
    if (kind in appState.settingsPanels) { appState.settingsPanels[kind] = true; syncSettingsPanels(); }
    openEditor(kind);
    return;
  }
  const closeTarget = event.target.closest("[data-close-modal]");
  if (closeTarget) { closeModal(); return; }
  const opKindTarget = event.target.closest("[data-op-kind]");
  if (opKindTarget) { setOpKind(opKindTarget.dataset.opKind); return; }
  const itemKindTarget = event.target.closest("[data-item-kind]");
  if (itemKindTarget) { setItemKind(itemKindTarget.dataset.itemKind); return; }
  const action = event.target.closest("[data-action]");
  if (!action) return;
  try {
    if (["earn", "deduct", "exchange"].includes(action.dataset.action)) await handleOperation(action.dataset.action, Number(action.dataset.id));
    if (action.dataset.action === "edit") openEditor(action.dataset.kind, Number(action.dataset.id));
    if (action.dataset.action === "delete") await deleteItem(action.dataset.kind, Number(action.dataset.id));
    if (action.dataset.action === "edit-account") openEditAccount(Number(action.dataset.id));
    if (action.dataset.action === "delete-account") await deleteAccount(Number(action.dataset.id));
    if (action.dataset.action === "approve-request") await reviewRequest("approve", Number(action.dataset.id));
    if (action.dataset.action === "reject-request") await reviewRequest("reject", Number(action.dataset.id));
    if (action.dataset.action === "claim-task") await handleTaskAction("claim", Number(action.dataset.id));
    if (action.dataset.action === "submit-task") await handleTaskAction("submit", Number(action.dataset.id));
    if (action.dataset.action === "edit-task") startTaskEdit(Number(action.dataset.id));
    if (action.dataset.action === "delete-task") await deleteTask(Number(action.dataset.id));
    if (action.dataset.action === "batch-delete-tasks") await batchDeleteDoneTasks();
    if (action.dataset.action === "approve-task") await handleTaskAction("approve", Number(action.dataset.id));
    if (action.dataset.action === "reject-task") await handleTaskAction("reject", Number(action.dataset.id));
    if (action.dataset.action === "edit-announcement") openAnnouncementEdit(Number(action.dataset.id));
    if (action.dataset.action === "delete-announcement") await deleteAnnouncement(Number(action.dataset.id));
    if (action.dataset.action === "undo") await undoRecord(Number(action.dataset.id));
    if (action.dataset.action === "export") await exportFamilyData();
  } catch (error) { showToast(error.message); }
});

document.addEventListener("submit", async (event) => {
  if (event.target.matches("[data-kind]")) {
    event.preventDefault();
    try { await handleOperation(event.target.dataset.kind, null, event.target); } catch (error) { showToast(error.message); }
  }
});

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await api("/api/auth/login", { method: "POST", body: JSON.stringify({ username: form.elements.username.value.trim(), password: form.elements.password.value }) });
    form.reset();
    appState.page = "home";
    await loadState();
  } catch (error) { document.getElementById("login-error").textContent = error.message; }
});

document.getElementById("child-register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const error = document.getElementById("child-register-error");
  error.textContent = "";
  if (form.elements.password.value !== form.elements.password_confirm.value) {
    error.textContent = "两次输入的密码不一致";
    return;
  }
  try {
    await api("/api/auth/register-child", {
      method: "POST",
      body: JSON.stringify({
        username: form.elements.username.value.trim(),
        display_name: form.elements.display_name.value.trim(),
        password: form.elements.password.value,
        password_confirm: form.elements.password_confirm.value,
        avatar: form.elements.avatar.value,
      }),
    });
    form.reset();
    await loadState();
  } catch (requestError) {
    error.textContent = requestError.message;
  }
});

document.getElementById("setup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const error = document.getElementById("setup-error");
  error.textContent = "";
  if (form.elements.password.value !== form.elements.password_confirm.value) {
    error.textContent = "两次输入的密码不一致";
    return;
  }
  try {
    await api("/api/setup/admin", {
      method: "POST",
      body: JSON.stringify({
        username: form.elements.username.value.trim(),
        password: form.elements.password.value,
        password_confirm: form.elements.password_confirm.value,
      }),
    });
    form.reset();
    await loadState();
  } catch (requestError) {
    error.textContent = requestError.message;
  }
});

document.getElementById("editor-form").addEventListener("submit", saveEditor);
document.getElementById("manual-form").addEventListener("submit", saveManual);
document.getElementById("account-form").addEventListener("submit", saveAccount);
document.getElementById("self-password-form").addEventListener("submit", saveSelfPassword);
document.getElementById("currency-form").addEventListener("submit", saveCurrencySettings);
document.getElementById("adventure-level-form")?.addEventListener("submit", saveAdventureLevel);
document.getElementById("quest-form").addEventListener("submit", saveTask);
document.getElementById("announcement-form")?.addEventListener("submit", saveAnnouncement);
document.getElementById("cash-exchange-form").addEventListener("submit", saveCashExchange);
document.querySelector("#cash-exchange-form input[name='points']").addEventListener("input", updateCashExchangePreview);
document.getElementById("announcement-popup-close")?.addEventListener("click", closeAnnouncementPopup);
document.getElementById("announcement-popup-ack")?.addEventListener("click", closeAnnouncementPopup);
document.getElementById("icon-search")?.addEventListener("input", renderIconPicker);
document.getElementById("quest-icon-search")?.addEventListener("input", renderQuestIconPicker);
document.getElementById("cancel-announcement-edit")?.addEventListener("click", () => {
  resetAnnouncementEditor();
  appState.announcementFormOpen = true;
  syncAnnouncementEditor();
});
document.getElementById("quest-cancel-edit")?.addEventListener("click", () => {
  appState.taskEditId = null;
  resetQuestForm();
  showToast("已退出编辑");
});
document.getElementById("open-account").addEventListener("click", openAccount);
document.getElementById("open-manual").addEventListener("click", openManual);
document.getElementById("open-self-password").addEventListener("click", openSelfPassword);
document.getElementById("open-child-register").addEventListener("click", showChildRegister);
document.getElementById("back-to-login").addEventListener("click", showLogin);
document.getElementById("account-form").elements.role.addEventListener("change", (event) => {
  fillAvatarOptions(event.target.value);
  document.getElementById("account-limit-field").classList.toggle("hidden", event.target.value !== "child");
});
document.getElementById("adventure-level-form")?.elements.mode.addEventListener("change", (event) => {
  const level = document.getElementById("adventure-level-form")?.elements.level;
  if (level) level.disabled = event.target.value !== "manual";
});
document.getElementById("logout-button").addEventListener("click", async () => { try { await api("/api/auth/logout", { method: "POST" }); } finally { showLogin(); } });
document.getElementById("child-select").addEventListener("change", async (event) => {
  try { appState.data = await api("/api/auth/select-child", { method: "POST", body: JSON.stringify({ child_id: Number(event.target.value) }) }); navigate("home"); showToast(`已切换到 ${appState.data.active_child.display_name}`); } catch (error) { showToast(error.message); }
});
document.getElementById("home-tabs")?.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-home-tab]");
  if (!tab) return;
  appState.homeTab = tab.dataset.homeTab;
  syncHomeTabs();
});
document.getElementById("toggle-announcement-editor")?.addEventListener("click", () => {
  appState.announcementFormOpen = !appState.announcementFormOpen;
  syncAnnouncementEditor();
  if (appState.announcementFormOpen) document.querySelector("#announcement-form input[name='title']")?.focus();
});
document.getElementById("toggle-account-detail")?.addEventListener("click", () => {
  appState.accountDetailOpen = !appState.accountDetailOpen;
  syncAccountDetail();
});
// v0.13.2：账号卡片折叠 —— 记录展开状态（toggle 不冒泡，用捕获阶段监听），并支持一键全部展开/收起
document.getElementById("account-summary-body")?.addEventListener("toggle", (event) => {
  const card = event.target.closest?.("details.account-card");
  if (card) appState.openAccounts[String(card.dataset.accountId)] = card.open;
}, true);
// v0.13.5 任务归档：折叠状态要跨重渲染保留（toggle 不冒泡，用捕获阶段监听）
document.getElementById("quest-list")?.addEventListener("toggle", (event) => {
  const panel = event.target.closest?.("details.quest-done-panel");
  if (panel) appState.questDoneOpen = panel.open;
}, true);
// v0.13.5 批量删除的勾选：单个勾选 / 全选，勾完即时刷新工具条计数
document.addEventListener("change", (event) => {
  const pick = event.target.closest("[data-pick-task]");
  if (pick) {
    const id = Number(pick.dataset.pickTask);
    const picked = new Set(appState.pickedDoneTasks);
    if (pick.checked) picked.add(id); else picked.delete(id);
    appState.pickedDoneTasks = [...picked];
    renderQuests();
    return;
  }
  if (event.target.id === "quest-pick-all") {
    const boxes = [...document.querySelectorAll("#quest-done-panel [data-pick-task]")];
    appState.pickedDoneTasks = event.target.checked ? boxes.map((node) => Number(node.dataset.pickTask)) : [];
    renderQuests();
  }
});
document.getElementById("toggle-account-cards")?.addEventListener("click", (event) => {
  const list = document.getElementById("account-summary-body");
  if (!list) return;
  const cards = [...list.querySelectorAll("details.account-card")];
  if (!cards.length) return;
  const expand = cards.some((card) => !card.open);
  cards.forEach((card) => { card.open = expand; });
  event.currentTarget.textContent = expand ? "全部收起" : "全部展开";
  event.currentTarget.setAttribute("aria-expanded", expand ? "true" : "false");
});
document.querySelectorAll("[data-toggle-settings-panel]").forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.toggleSettingsPanel;
    appState.settingsPanels[key] = !appState.settingsPanels[key];
    syncSettingsPanels();
  });
});
document.getElementById("prev-month").addEventListener("click", () => { if (appState.historyMonth === 0) { appState.historyMonth = 11; appState.historyYear -= 1; } else appState.historyMonth -= 1; renderHistory(); });
document.getElementById("next-month").addEventListener("click", () => { if (appState.historyMonth === 11) { appState.historyMonth = 0; appState.historyYear += 1; } else appState.historyMonth += 1; renderHistory(); });
document.getElementById("modal-backdrop").addEventListener("click", (event) => { if (event.target.id === "modal-backdrop") closeModal(); });
document.getElementById("confirm-cancel").addEventListener("click", () => settleConfirm(false));
document.getElementById("confirm-close").addEventListener("click", () => settleConfirm(false));
document.getElementById("confirm-submit").addEventListener("click", () => settleConfirm(true));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !document.getElementById("modal-backdrop").classList.contains("hidden")) closeModal();
});
// v0.13.0 覆盖式导入：先自动备份当前整库，再整体替换为备份文件内容
document.getElementById("import-data").addEventListener("click", () => document.getElementById("import-file").click());
document.getElementById("import-file").addEventListener("change", async (event) => {
  const input = event.target;
  const file = input.files && input.files[0];
  input.value = "";                       // 清空后同一个文件才能再次触发 change
  if (!file) return;
  try {
    const text = await file.text();
    const ok = await requestConfirm(`导入会覆盖当前全部数据（账号、积分记录、任务、项目设置），导入前会自动备份一份。确定导入「${file.name}」吗？`, { title: "导入家庭数据", confirmLabel: "确认导入" });
    if (!ok) return;
    const result = await api("/api/import", { method: "POST", body: text });
    if (result.relogin) {                 // 导入的是别处的数据，当前管理账号已不存在
      showToast("导入完成，请用备份文件里的账号重新登录");
      showLogin();
      return;
    }
    appState.data = result.state;
    render();
    showToast(result.backup ? "导入完成，旧数据已自动备份到 data/backups" : "导入完成");
  } catch (error) { showToast(error.message); }
});
document.getElementById("clear-points").addEventListener("click", async () => {
  if (!await requestConfirm("确定清空当前孩子的全部积分记录吗？", { title: "清空积分记录", confirmLabel: "清空记录" })) return;
  try { appState.data = await api("/api/system/clear", { method: "POST" }); render(); showToast("积分记录已清空"); } catch (error) { showToast(error.message); }
});
document.getElementById("reset-system").addEventListener("click", async () => {
  if (!await requestConfirm("确定恢复当前孩子的默认设置吗？", { title: "恢复默认设置", confirmLabel: "恢复默认" })) return;
  try { appState.data = await api("/api/system/reset", { method: "POST" }); render(); showToast("当前孩子已恢复默认设置"); } catch (error) { showToast(error.message); }
});

renderQuestIconPicker();
setupRepeatForm();
syncTaskFormMode();
setupTheme();
startConnectionMonitor();
loadState();
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}

function applyTableLabels() {
  document.querySelectorAll(".management-table").forEach((table) => {
    const headers = [...table.querySelectorAll("thead th")].map((th) => th.textContent.trim());
    table.querySelectorAll("tbody tr").forEach((tr) => {
      const cells = tr.children;
      for (let i = 0; i < cells.length; i += 1) {
        cells[i].setAttribute("data-label", headers[i] || "");
      }
    });
  });
}

function startConnectionMonitor() {
  const indicator = document.getElementById("connection-state");
  if (!indicator) return;
  indicator.dataset.monitorReady = "1";
  async function poll() {
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      if (!res.ok) throw new Error("bad status");
      indicator.textContent = "已连接";
      indicator.classList.add("is-online");
      indicator.classList.remove("is-offline");
    } catch (_error) {
      indicator.textContent = "连接异常";
      indicator.classList.add("is-offline");
      indicator.classList.remove("is-online");
    }
  }
  poll();
  setInterval(poll, 30000);
  setInterval(() => syncState({ force: true }), 60000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      poll();
      syncState({ force: true });
    }
  });
  window.addEventListener("focus", () => syncState());
}

function setupTheme() {
  const button = document.getElementById("theme-toggle");
  function apply(theme) {
    if (theme === "dark") document.documentElement.dataset.theme = "dark";
    else delete document.documentElement.dataset.theme;
    if (button) button.textContent = theme === "dark" ? "☀ 浅色" : "🌙 深色";
  }
  let saved = "light";
  try { saved = localStorage.getItem("rewardhub-theme") || "light"; } catch (_error) {}
  apply(saved);
  button?.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem("rewardhub-theme", next); } catch (_error) {}
  });
}

async function exportFamilyData() {
  if (appState.data?.user?.role !== "admin") {
    showToast("仅管理账号可导出家庭数据");
    return;
  }
  try {
    const res = await fetch("/api/export");
    if (res.status === 401) { showLogin(); return; }
    if (!res.ok) throw new Error("导出失败");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    a.href = url;
    a.download = `rewardhub-家庭数据-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast("家庭数据已导出");
  } catch (error) {
    showToast(error.message || "导出失败");
  }
}

let celebrationBaseline = null;
function detectCelebration(data) {
  const gamification = data.gamification || {};
  const level = Number(gamification.level || 1);
  const ids = new Set((data.achievements || []).filter((a) => a.unlocked).map((a) => a.id));
  if (!celebrationBaseline) { celebrationBaseline = { level, ids }; return; }
  if (level > celebrationBaseline.level) celebrate(`升级到 LV ${level}！`);
  ids.forEach((id) => { if (!celebrationBaseline.ids.has(id)) celebrate("解锁新成就！"); });
  celebrationBaseline = { level, ids };
}

function celebrate(message) {
  const overlay = document.getElementById("celebration");
  if (!overlay) return;
  const text = overlay.querySelector(".celebration-text");
  if (text) text.textContent = message;
  overlay.classList.remove("hidden");
  requestAnimationFrame(() => overlay.classList.add("show"));
  clearTimeout(celebrate.timer);
  celebrate.timer = setTimeout(() => {
    overlay.classList.remove("show");
    setTimeout(() => overlay.classList.add("hidden"), 300);
  }, 2400);
}
