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
};

let confirmResolver = null;

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
    showApp();
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
  document.getElementById("connection-state").textContent = "数据库已连接";
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
  document.getElementById("nav-requests-label").textContent = isAdmin ? "审核" : "申请";
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
  const adminPages = ["deduct", "accounts", "settings"];
  if (adminPages.includes(page) && !isAdmin) page = "home";
  appState.page = page;
  document.querySelectorAll(".page").forEach((element) => element.classList.toggle("active", element.dataset.page === page));
  document.querySelectorAll(".nav-button").forEach((element) => element.classList.toggle("active", element.dataset.pageTarget === page));
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
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
  renderQuests();
  renderQuestFocus();
  renderAnnouncements();
  renderAchievements();
  renderAccounts();
  renderRecords();
  updateCurrencyUi();
  updateCashExchangeDiscount();
  updateCashExchangePreview();
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
  const pending = children.reduce((sum, item) => sum + Number(item.pending_count), 0);
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
  document.getElementById("earn-target-name").textContent = account.display_name || "暂无孩子账号";
  document.getElementById("deduct-target-name").textContent = account.display_name || "暂无孩子账号";
  document.getElementById("pending-action-label").textContent = `${pending} 条待处理`;
  document.querySelector(".hero-actions.admin-only")?.classList.toggle("hidden", user.role !== "admin" || !hasChild);
  document.getElementById("no-child-panel")?.classList.toggle("hidden", !(user.role === "admin" && !hasChild));
  const metrics = user.role === "admin" ? [
    ["孩子账户", children.length, "个", "metric-green"],
    ["家庭总积分", children.reduce((sum, item) => sum + Number(item.total_points), 0), "分", "metric-blue"],
    ["待审核申请", pending, "条", pending ? "metric-orange" : "metric-green"],
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
    homeSummary.innerHTML = children.length ? children.map((child) => `<tr><td><div class="table-person">${avatarImage(child.avatar, "avatar avatar-table", child.display_name)}<div><strong>${escapeHtml(child.display_name)}</strong><small>${escapeHtml(child.username)}</small></div></div></td><td class="table-number">${Number(child.total_points).toLocaleString("zh-CN")}</td><td class="table-number">${moneyText(child.total_points)}</td><td class="table-number ${Number(child.today_net) >= 0 ? "income" : "expense"}">${signed(child.today_net)}</td><td><span class="pending-badge">${Number(child.pending_count)}</span></td><td><span class="status-pill ${Number(child.pending_count) ? "status-pending" : "status-approved"}">${Number(child.pending_count) ? "待审核" : "运行正常"}</span></td></tr>`).join("") : `<tr><td colspan="6"><div class="empty-state">暂无孩子账号，请先创建账号</div></td></tr>`;
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
  document.getElementById("requests-title").textContent = isAdmin ? "审核申请" : "我的申请";
  document.getElementById("requests-subtitle").textContent = isAdmin ? "孩子提交的赚积分或兑换申请，审核后才会更新余额。" : "申请不会直接改变余额，等待管理账号审核。";
  const requests = appState.data.requests || [];
  document.getElementById("requests-list").innerHTML = requests.length ? requests.map(requestMarkup).join("") : `<div class="empty-state">暂无申请记录</div>`;
}

const TASK_DIFFICULTY_TEXT = { easy: "简单", normal: "普通", hard: "困难", legendary: "传说" };
const TASK_TYPE_TEXT = { daily: "日常任务", epic: "史诗悬赏" };
const TASK_STATUS_TEXT = { claimed: "已领取", submitted: "待验收", completed: "已完成", rejected: "需重做" };

function taskActionMarkup(task) {
  const isAdmin = appState.data.user.role === "admin";
  if (isAdmin) {
    const pending = (task.assignments || []).filter((assignment) => assignment.status === "submitted");
    return pending.length ? `<span class="quest-status quest-status-submitted">${pending.length} 人待验收</span>` : `<span class="muted">${task.participant_count || 0} 人参与</span>`;
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

function renderQuests() {
  const list = document.getElementById("quest-list");
  if (!list) return;
  const tasks = appState.data.tasks || [];
  if (!tasks.length) {
    list.innerHTML = `<div class="content-panel empty-state">暂无悬赏任务，管理员可以在上方发布第一个任务。</div>`;
    return;
  }
  list.innerHTML = tasks.map((task) => {
    const assignments = appState.data.user.role === "admin" && task.assignments?.length ? `<div class="quest-assignees">${task.assignments.map(questAssignmentMarkup).join("")}</div>` : "";
    const due = task.due_date ? `截止 ${escapeHtml(task.due_date)}` : "长期有效";
    const rewardCoins = Number(task.reward_coins);
    const baseReward = Number(task.base_reward_coins || rewardCoins);
    const rewardNote = baseReward !== rewardCoins ? `<small class="quest-reward-note">基础 ${baseReward.toLocaleString("zh-CN")}</small>` : "";
    return `<article class="quest-card ${task.task_type === "epic" ? "epic" : ""}"><div class="quest-card-head"><div class="quest-card-title">${iconMarkup(task.icon, "earn", "quest-icon") }<div><h2>${escapeHtml(task.title)}</h2><p>${escapeHtml(task.category)} · ${TASK_TYPE_TEXT[task.task_type] || task.task_type}</p></div></div><span class="quest-rarity">${TASK_DIFFICULTY_TEXT[task.difficulty] || task.difficulty}</span></div><p class="quest-description">${escapeHtml(task.description || "完成任务后提交，等待管理员验收。")}</p><div class="quest-card-meta"><span class="quest-reward">◆ ${rewardCoins.toLocaleString("zh-CN")} 积分${rewardNote}</span><span class="quest-reward">✦ ${Number(task.reward_exp).toLocaleString("zh-CN")} XP</span><span class="muted">${due}</span></div><div class="quest-card-actions">${taskActionMarkup(task)}</div>${assignments}</article>`;
  }).join("");
}

function renderQuestFocus() {
  const focus = document.getElementById("child-quest-focus");
  if (!focus) return;
  const task = (appState.data.tasks || []).find((item) => item.task_type === "epic") || (appState.data.tasks || [])[0];
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
  const actionState = !assignment ? { action: "claim-task", id: task.id, label: "领取任务" } : assignment.status === "claimed" || assignment.status === "rejected" ? { action: "submit-task", id: assignment.id, label: assignment.status === "rejected" ? "重新提交" : "提交验收" } : { action: "", id: "", label: TASK_STATUS_TEXT[assignment.status] || assignment.status };
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
  form.querySelector("button[type='submit']").textContent = "发布通告";
  document.getElementById("cancel-announcement-edit")?.classList.add("hidden");
}

function openAnnouncementEdit(id) {
  const announcement = (appState.data.announcements || []).find((item) => Number(item.id) === Number(id));
  const form = document.getElementById("announcement-form");
  if (!announcement || !form) return;
  appState.announcementEditId = Number(id);
  form.elements.announcement_id.value = announcement.id;
  form.elements.title.value = announcement.title;
  form.elements.content.value = announcement.content;
  form.elements.audience.value = announcement.audience;
  form.querySelector("button[type='submit']").textContent = "保存通告";
  document.getElementById("cancel-announcement-edit")?.classList.remove("hidden");
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

function renderAccounts() {
  const summaryBody = document.getElementById("account-summary-body");
  const logBody = document.getElementById("account-log-body");
  if (!summaryBody || !logBody || appState.data.user.role !== "admin") return;
  const currentId = Number(appState.data.user.id);
  const overview = appState.data.account_overview || [];
  summaryBody.innerHTML = overview.length ? overview.map((account) => {
    const isChild = account.role === "child";
    const deleteButton = Number(account.id) === currentId ? "" : `<button class="button button-small button-outline-danger" data-action="delete-account" data-id="${account.id}" type="button">删除</button>`;
    const action = `<div class="row-actions"><button class="button button-small button-outline" data-action="edit-account" data-id="${account.id}" type="button">编辑</button>${deleteButton}</div>`;
    return `<tr><td><div class="table-person">${avatarImage(account.avatar, "avatar avatar-table", account.display_name)}<div><strong>${escapeHtml(account.display_name)}</strong><small>${escapeHtml(account.avatar === "girl" ? "女孩头像" : account.avatar === "boy" ? "男孩头像" : "管理头像")}</small></div></div></td><td>${escapeHtml(account.username)}</td><td>${isChild ? "孩子账号" : "管理账号"}</td><td class="table-number">${Number(account.total_points).toLocaleString("zh-CN")}</td><td class="table-number">${moneyText(account.total_points)}</td><td class="table-number ${Number(account.today_net) >= 0 ? "income" : "expense"}">${signed(account.today_net)}</td><td><span class="pending-badge">${Number(account.pending_count)}</span></td><td>${action}</td></tr>`;
  }).join("") : `<tr><td colspan="8"><div class="empty-state">暂无账号</div></td></tr>`;
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
    ? `实际扣除 ${chargedPoints.toLocaleString("zh-CN")} 积分（原需 ${basePoints.toLocaleString("zh-CN")}，省 ${savedPoints.toLocaleString("zh-CN")}）`
    : `实际扣除 ${chargedPoints.toLocaleString("zh-CN")} 积分`;
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

async function saveTask(event) {
  event.preventDefault();
  const form = event.currentTarget;
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
  try {
    const result = await api("/api/tasks", { method: "POST", body: JSON.stringify(payload) });
    appState.data = result.state;
    form.reset();
    form.elements.reward_coins.value = 20;
    form.elements.reward_exp.value = 10;
    render();
    showToast("悬赏任务已发布");
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
  } catch (error) { showToast(error.message); }
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
  if (editorTarget) { openEditor(editorTarget.dataset.openEditor); return; }
  const closeTarget = event.target.closest("[data-close-modal]");
  if (closeTarget) { closeModal(); return; }
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
    if (action.dataset.action === "approve-task") await handleTaskAction("approve", Number(action.dataset.id));
    if (action.dataset.action === "reject-task") await handleTaskAction("reject", Number(action.dataset.id));
    if (action.dataset.action === "edit-announcement") openAnnouncementEdit(Number(action.dataset.id));
    if (action.dataset.action === "delete-announcement") await deleteAnnouncement(Number(action.dataset.id));
    if (action.dataset.action === "undo") await undoRecord(Number(action.dataset.id));
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
document.getElementById("cancel-announcement-edit")?.addEventListener("click", resetAnnouncementEditor);
document.getElementById("open-account").addEventListener("click", openAccount);
document.getElementById("open-manual").addEventListener("click", openManual);
document.getElementById("open-self-password").addEventListener("click", openSelfPassword);
document.getElementById("open-child-register").addEventListener("click", showChildRegister);
document.getElementById("back-to-login").addEventListener("click", showLogin);
document.getElementById("account-form").elements.role.addEventListener("change", (event) => fillAvatarOptions(event.target.value));
document.getElementById("adventure-level-form")?.elements.mode.addEventListener("change", (event) => {
  const level = document.getElementById("adventure-level-form")?.elements.level;
  if (level) level.disabled = event.target.value !== "manual";
});
document.getElementById("logout-button").addEventListener("click", async () => { try { await api("/api/auth/logout", { method: "POST" }); } finally { showLogin(); } });
document.getElementById("child-select").addEventListener("change", async (event) => {
  try { appState.data = await api("/api/auth/select-child", { method: "POST", body: JSON.stringify({ child_id: Number(event.target.value) }) }); navigate("home"); showToast(`已切换到 ${appState.data.active_child.display_name}`); } catch (error) { showToast(error.message); }
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
document.getElementById("clear-points").addEventListener("click", async () => {
  if (!await requestConfirm("确定清空当前孩子的全部积分记录吗？", { title: "清空积分记录", confirmLabel: "清空记录" })) return;
  try { appState.data = await api("/api/system/clear", { method: "POST" }); render(); showToast("积分记录已清空"); } catch (error) { showToast(error.message); }
});
document.getElementById("reset-system").addEventListener("click", async () => {
  if (!await requestConfirm("确定恢复当前孩子的默认设置吗？", { title: "恢复默认设置", confirmLabel: "恢复默认" })) return;
  try { appState.data = await api("/api/system/reset", { method: "POST" }); render(); showToast("当前孩子已恢复默认设置"); } catch (error) { showToast(error.message); }
});

renderQuestIconPicker();
loadState();
