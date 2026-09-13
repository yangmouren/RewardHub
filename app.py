from __future__ import annotations

import base64
import binascii
import calendar
import hashlib
import json
import math
import os
import re
import secrets
import time
from threading import Lock
import sqlite3
import sys
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Iterator

from flask import Flask, abort, jsonify, render_template, request, send_file, session


BASE_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
if getattr(sys, "frozen", False):
    DEFAULT_DATA_DIR = Path(sys.executable).resolve().parent / "data"
else:
    DEFAULT_DATA_DIR = BASE_DIR / "data"
DATA_DIR = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "points.db")))
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
PASSWORD_ITERATIONS = 240_000
APP_VERSION = "0.13.6"
AVATAR_OPTIONS = {"boy", "girl", "adult-male", "adult-female"}
CHILD_AVATARS = {"boy", "girl"}
PROJECT_ICONS = {
    "television.svg", "book.svg", "homework.svg", "chore.svg", "sport.svg",
    "bedtime.svg", "snack.svg", "game.svg", "outing.svg", "points.svg",
    "gift.svg", "warning.svg", "computer.svg", "desktop.svg", "money.svg",
    "phone.svg", "cooking.svg", "cleaning.svg", "school.svg", "toothbrush.svg",
    "bath.svg", "pencil.svg", "clothes.svg", "laundry.svg", "dishes.svg",
    "pet.svg", "walk.svg", "shopping.svg", "backpack.svg", "handwash.svg",
    "water.svg", "plant.svg", "tidy.svg", "trash.svg", "lunch.svg", "delivery.svg",
}
BUILTIN_ICON_KEYS = set(
    """
    home broom vacuum clean tidy trash laundry dishes clothes iron bed sleep alarm shower toothbrush handwash bath repair hammer screwdriver
    cooking meal breakfast lunch dinner bread rice noodles apple banana orange strawberry cake cookie milk water coffee tea juice snack icecream
    homework book reading pencil school graduation math science language art music idea microscope ruler notebook library exam medal target lightbulb
    sport run walk bike swim football basketball baseball tennis badminton yoga weight hiking mountain trophy whistle skate climbing fitness stretch
    car bus train airplane rocket ship taxi bicycle map location suitcase passport ticket traffic fuel travel compass road parking delivery
    family child baby adult dog cat pet plant flower birthday heart homekey door sofa tv camera phone calendar couple
    nas server harddrive folder cloud download upload wifi network database terminal code keyboard printer tablet desktop computer smartphone gamepad
    office briefcase clock chart mail meeting call checklist pin note moneybag contract build manager megaphone bell search settings shield lock
    coin money diamond crown badge star fire bolt gem treasure giftbox fireworks crown2 medal2
    doctor medicine hospital mask bandage thermometer apple2 water2 heart2 brain lungs health firstaid rest
    sun moon cloud2 rain snow rainbow wind leaf tree flower2 season umbrella temperature earth
    party confetti balloon cake2 music2 flag community handshake speech message announcement megaphone2 group friend smile package
    """.split()
)
ITEM_DEFAULT_ICONS = {"earn": "points.svg", "deduct": "warning.svg", "reward": "gift.svg"}
DEFAULT_SETTINGS = {"points_per_yuan": 100}
# 每日提交审核额度（v0.11.0）：按「当天提交总次数」计数，避免孩子端刷量把审核队列挤爆。
# 0 表示不限制；每个孩子账号独立配置，缺省 10 次。
DEFAULT_DAILY_SUBMIT_LIMIT = 10
MAX_DAILY_SUBMIT_LIMIT = 999
TASK_TYPES = {"daily", "epic", "repeat"}
TASK_DIFFICULTIES = {"easy", "normal", "hard", "legendary"}
# 重复任务（v0.9.0）：统一为「频率 + 星期几 + 第几个 + 有效期」四要素，不为个别场景开特例。
# - daily   ：每天都触发
# - weekly  ：每周的 repeat_days 指定星期几触发
# - monthly ：每月第 repeat_month_week 个 repeat_days 指定星期几触发（5 表示最后一个）
REPEAT_FREQUENCIES = {"daily", "weekly", "monthly"}
WEEKDAY_TEXT = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}
WEEKDAY_ORDER = (1, 2, 3, 4, 5, 6, 7)
LAST_WEEK_INDEX = 5
DEFAULT_ACHIEVEMENTS = [
    ("first-quest", "初次出征", "完成第一个现实任务", "points.svg", "completed_tasks", 1),
    ("habit-builder", "习惯养成", "完成 3 个任务，建立自己的节奏", "bedtime.svg", "completed_tasks", 3),
    ("quest-ten", "十次出征", "完成 10 个任务，成为可靠的冒险者", "backpack.svg", "completed_tasks", 10),
    ("quest-twenty-five", "任务老手", "完成 25 个任务，持续兑现自己的目标", "points.svg", "completed_tasks", 25),
    ("epic-clear", "史诗征服者", "完成第一个史诗悬赏", "gift.svg", "epic_tasks", 1),
    ("epic-trio", "史诗远征队", "完成 3 个史诗悬赏", "gift.svg", "epic_tasks", 3),
    ("epic-five", "传奇开拓者", "完成 5 个史诗悬赏", "gift.svg", "epic_tasks", 5),
    ("coin-hoard", "积分收藏家", "累计赚取 100 积分", "money.svg", "earned_coins", 100),
    ("coin-five-hundred", "积分宝库", "累计赚取 500 积分", "money.svg", "earned_coins", 500),
    ("coin-thousand", "财富领航员", "累计赚取 1000 积分", "money.svg", "earned_coins", 1000),
    ("daily-five", "日常坚持者", "完成 5 个日常任务", "bedtime.svg", "daily_tasks", 5),
]


def valid_project_icon(icon: str | None) -> bool:
    if not isinstance(icon, str):
        return False
    if icon in PROJECT_ICONS:
        return True
    return icon.startswith("emoji:") and icon[6:] in BUILTIN_ICON_KEYS

DEFAULT_EARN_ITEMS = [
    ("完成作业", 10, "homework.svg"),
    ("阅读30分钟", 5, "book.svg"),
    ("做家务", 15, "chore.svg"),
    ("锻炼身体", 8, "sport.svg"),
    ("早睡早起", 5, "bedtime.svg"),
]
DEFAULT_DEDUCT_ITEMS = [
    ("未完成作业", 10, "warning.svg"),
    ("迟到", 5, "warning.svg"),
    ("说脏话", 8, "warning.svg"),
    ("不整理房间", 5, "chore.svg"),
]
DEFAULT_REWARDS = [
    ("看电视30分钟", 50, "television.svg"),
    ("玩游戏1小时", 100, "game.svg"),
    ("买零食", 30, "snack.svg"),
    ("周末外出", 200, "outing.svg"),
]
ITEM_TABLES = {"earn": "earn_items", "deduct": "deduct_items", "reward": "rewards"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
CUSTOM_ASSET_KEYS = {
    "child-boy", "child-girl", "adult-male", "adult-female",
    "account-log", "login-cover", "control-center",
}
CUSTOM_IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}



@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("ascii"), PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def password_matches(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("ascii"), int(iterations)
        ).hex()
        return secrets.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def environment_value(name: str) -> str:
    """Read an optional base64 value before the plain environment variable.

    FlyNAS stores wizard passwords in an env file. Base64 keeps characters such
    as `$`, `#`, quotes, and spaces from being reinterpreted by Compose.
    """
    encoded = os.getenv(f"{name}_B64", "").strip()
    if encoded:
        try:
            return base64.b64decode(encoded, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            return ""
    return os.getenv(name, "")


def admin_credentials_from_env() -> tuple[str, str] | None:
    username = environment_value("ADMIN_USERNAME").strip()
    password = environment_value("ADMIN_PASSWORD")
    if not username and not password:
        return None
    if not USERNAME_PATTERN.fullmatch(username) or len(password) < 6:
        return None
    return username, password


def admin_credentials_fingerprint(credentials: tuple[str, str]) -> str:
    """Return a non-reversible marker for the last applied install credentials."""
    username, password = credentials
    payload = f"{username}\0{password}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def admin_credentials_marker_path() -> Path:
    return DATA_DIR / ".admin-credentials.applied"


def install_credentials_are_applied(credentials: tuple[str, str]) -> bool:
    marker = admin_credentials_marker_path()
    try:
        return marker.read_text(encoding="ascii").strip() == admin_credentials_fingerprint(credentials)
    except (OSError, UnicodeError):
        return False


def mark_install_credentials_applied(credentials: tuple[str, str]) -> None:
    marker = admin_credentials_marker_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    temp_marker = marker.with_name(f"{marker.name}.{os.getpid()}.tmp")
    temp_marker.write_text(admin_credentials_fingerprint(credentials), encoding="ascii")
    temp_marker.replace(marker)


def create_admin_account(conn: sqlite3.Connection, username: str, password: str) -> sqlite3.Row:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO accounts(username, password_hash, display_name, role, avatar, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (username, password_hash(password), "管理员", "admin", "adult-male", now),
    )
    return conn.execute("SELECT * FROM accounts WHERE username = ?", (username,)).fetchone()


def migrate_legacy_admin_account(conn: sqlite3.Connection) -> None:
    """Replace only the untouched admin/admin123 account with install-time credentials."""
    credentials = admin_credentials_from_env()
    if credentials is None:
        return
    admin = conn.execute(
        "SELECT * FROM accounts WHERE role = 'admin' AND active = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if admin is None or admin["username"] != "admin":
        return
    if not password_matches("admin123", admin["password_hash"]):
        return
    username, password = credentials
    if username == "admin" and password == "admin123":
        return
    try:
        conn.execute(
            "UPDATE accounts SET username = ?, password_hash = ?, display_name = ? WHERE id = ?",
            (username, password_hash(password), "管理员", admin["id"]),
        )
    except sqlite3.IntegrityError:
        # Never replace a real account that already uses the requested username.
        return


def apply_install_admin_credentials(conn: sqlite3.Connection, credentials: tuple[str, str]) -> bool:
    """Apply install-wizard credentials once without deleting application data."""
    username, password = credentials
    requested = conn.execute(
        "SELECT * FROM accounts WHERE username = ? AND active = 1", (username,)
    ).fetchone()
    if requested is not None and requested["role"] != "admin":
        return False

    if requested is not None:
        conn.execute(
            "UPDATE accounts SET password_hash = ? WHERE id = ?",
            (password_hash(password), requested["id"]),
        )
        return True

    admin = conn.execute(
        "SELECT * FROM accounts WHERE role = 'admin' AND active = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if admin is None:
        create_admin_account(conn, username, password)
        return True

    try:
        conn.execute(
            "UPDATE accounts SET username = ?, password_hash = ? WHERE id = ?",
            (username, password_hash(password), admin["id"]),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row["name"] == column for row in conn.execute(f"PRAGMA table_info({table})").fetchall())


def migrate_point_requests(conn: sqlite3.Connection) -> None:
    schema = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'point_requests'"
    ).fetchone()
    if schema is None or "cash_exchange" in (schema["sql"] or ""):
        return
    conn.execute("ALTER TABLE point_requests RENAME TO point_requests_legacy")
    conn.execute(
        """
        CREATE TABLE point_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('earn', 'deduct', 'exchange', 'cash_exchange', 'manual')),
            title TEXT NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            reviewer_id INTEGER,
            reject_reason TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO point_requests(
            id, account_id, requester_id, kind, title, amount, type, date, time,
            status, created_at, reviewed_at, reviewer_id, reject_reason
        )
        SELECT id, account_id, requester_id, kind, title, amount, type, date, time,
               status, created_at, reviewed_at, reviewer_id, reject_reason
        FROM point_requests_legacy
        """
    )
    conn.execute("DROP TABLE point_requests_legacy")


def seed_items_for_child(conn: sqlite3.Connection, account_id: int) -> None:
    defaults = (
        ("earn_items", DEFAULT_EARN_ITEMS),
        ("deduct_items", DEFAULT_DEDUCT_ITEMS),
        ("rewards", DEFAULT_REWARDS),
    )
    for table, items in defaults:
        if conn.execute(f"SELECT COUNT(*) FROM {table} WHERE account_id = ?", (account_id,)).fetchone()[0] == 0:
            conn.executemany(
                f"INSERT INTO {table}(account_id, name, points, icon) VALUES (?, ?, ?, ?)",
                [(account_id, name, points, icon) for name, points, icon in items],
            )


def migrate_tasks_repeat(conn: sqlite3.Connection) -> None:
    """v0.9.0：让 tasks 支持「重复任务」。

    老库的 task_type 上带着 CHECK(task_type IN ('daily','epic'))，SQLite 不能直接改约束，
    所以需要重建表。新库由 CREATE TABLE 自带重复字段，这里只在缺列时才会真正执行。
    """
    if table_has_column(conn, "tasks", "repeat_freq"):
        return
    # task_assignments 未声明外键（仅 task_id 列），重命名不会破坏引用
    conn.execute("ALTER TABLE tasks RENAME TO tasks_legacy")
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '生活',
            task_type TEXT NOT NULL CHECK (task_type IN ('daily', 'epic', 'repeat')),
            difficulty TEXT NOT NULL DEFAULT 'normal' CHECK (difficulty IN ('easy', 'normal', 'hard', 'legendary')),
            reward_coins INTEGER NOT NULL CHECK (reward_coins > 0),
            reward_exp INTEGER NOT NULL CHECK (reward_exp > 0),
            icon TEXT NOT NULL DEFAULT 'points.svg',
            due_date TEXT,
            created_by INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            repeat_freq TEXT,
            repeat_days TEXT,
            repeat_month_week INTEGER,
            repeat_start TEXT,
            repeat_end TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO tasks(
            id, title, description, category, task_type, difficulty, reward_coins, reward_exp,
            icon, due_date, created_by, is_active, created_at,
            repeat_freq, repeat_days, repeat_month_week, repeat_start, repeat_end
        )
        SELECT
            id, title, description, category, task_type, difficulty, reward_coins, reward_exp,
            icon, due_date, created_by, is_active, created_at,
            NULL, NULL, NULL, NULL, NULL
        FROM tasks_legacy
        """
    )
    conn.execute("DROP TABLE tasks_legacy")


# ---------------------------------------------------------------------------
# 重复任务（v0.9.0）
# ---------------------------------------------------------------------------


def parse_weekday_list(raw: Any) -> list[int]:
    """把 '1,2,3' / [1,2,3] 解析成有序去重的星期列表（1=周一 ... 7=周日）。"""
    if raw is None or raw == "":
        return []
    if isinstance(raw, (list, tuple, set)):
        parts = list(raw)
    else:
        parts = [piece for piece in re.split(r"[,\s]+", str(raw)) if piece]
    days: list[int] = []
    for piece in parts:
        try:
            value = int(piece)
        except (TypeError, ValueError) as exc:
            raise ValueError("星期选择无效") from exc
        if value not in WEEKDAY_TEXT:
            raise ValueError("星期选择无效")
        if value not in days:
            days.append(value)
    return [day for day in WEEKDAY_ORDER if day in days]


def normalize_repeat_rule(payload: dict[str, Any], task_type: str) -> dict[str, Any]:
    """校验并归一化重复规则。task_type 不是 repeat 时返回全空值。"""
    empty = {
        "repeat_freq": None,
        "repeat_days": None,
        "repeat_month_week": None,
        "repeat_start": None,
        "repeat_end": None,
    }
    if task_type != "repeat":
        return empty
    freq = str(payload.get("repeat_freq") or "daily").strip().lower()
    if freq not in REPEAT_FREQUENCIES:
        raise ValueError("重复频率无效")
    days = parse_weekday_list(payload.get("repeat_days"))
    month_week: int | None = None
    if freq in ("weekly", "monthly") and not days:
        raise ValueError("每周/每月重复至少要选择一个星期")
    if freq == "monthly":
        try:
            month_week = int(payload.get("repeat_month_week") or 1)
        except (TypeError, ValueError) as exc:
            raise ValueError("「第几个」必须是数字") from exc
        if not 1 <= month_week <= LAST_WEEK_INDEX:
            raise ValueError(f"「第几个」需要在 1 到 {LAST_WEEK_INDEX} 之间（{LAST_WEEK_INDEX} 表示最后一个）")
    start_raw = str(payload.get("repeat_start") or "").strip()
    end_raw = str(payload.get("repeat_end") or "").strip()
    try:
        start = date.fromisoformat(start_raw).isoformat() if start_raw else None
        end = date.fromisoformat(end_raw).isoformat() if end_raw else None
    except ValueError as exc:
        raise ValueError("重复生效日期格式必须为 YYYY-MM-DD") from exc
    if start and end and end < start:
        raise ValueError("重复结束日期不能早于开始日期")
    return {
        "repeat_freq": freq,
        "repeat_days": ",".join(str(day) for day in days) if days else None,
        "repeat_month_week": month_week,
        "repeat_start": start,
        "repeat_end": end,
    }


def nth_weekday_of_month(day: date, weekday: int) -> int:
    """day 是当月的第几个「weekday」（1 起）。"""
    return (day.day - 1) // 7 + 1


def is_last_weekday_of_month(day: date) -> bool:
    return day.day + 7 > calendar.monthrange(day.year, day.month)[1]


def repeat_matches(task: sqlite3.Row | dict[str, Any], day: date) -> bool:
    """判断某个重复任务在 `day` 这天是否触发。"""
    freq = (task["repeat_freq"] or "").strip().lower()
    if freq not in REPEAT_FREQUENCIES:
        return False
    if task["repeat_start"] and day.isoformat() < task["repeat_start"]:
        return False
    if task["repeat_end"] and day.isoformat() > task["repeat_end"]:
        return False
    if freq == "daily":
        return True
    days = parse_weekday_list(task["repeat_days"])
    if day.isoweekday() not in days:
        return False
    if freq == "weekly":
        return True
    # monthly：第 repeat_month_week 个该星期几（LAST_WEEK_INDEX 表示最后一个）
    nth = int(task["repeat_month_week"] or 1)
    if nth >= LAST_WEEK_INDEX:
        return is_last_weekday_of_month(day)
    return nth_weekday_of_month(day, day.isoweekday()) == nth


def repeat_rule_text(task: sqlite3.Row | dict[str, Any]) -> str:
    """把重复规则渲染成一句人话，例如「每周一、三、五」「每月第 1 个周六、周日」。"""
    freq = (task["repeat_freq"] or "").strip().lower()
    if freq not in REPEAT_FREQUENCIES:
        return ""
    if freq == "daily":
        text = "每天"
    else:
        days = parse_weekday_list(task["repeat_days"])
        names = "、".join(WEEKDAY_TEXT[day].replace("周", "") for day in days)
        if freq == "weekly":
            text = f"每周{names}"
        else:
            nth = int(task["repeat_month_week"] or 1)
            label = "最后一个" if nth >= LAST_WEEK_INDEX else f"第 {nth} 个"
            text = f"每月{label}周{names}"
    window = []
    if task["repeat_start"]:
        window.append(f"{task['repeat_start'][5:]} 起")
    if task["repeat_end"]:
        window.append(f"{task['repeat_end'][5:]} 止")
    if window:
        text += f"（{'，'.join(window)}）"
    return text


def next_repeat_occurrence(task: sqlite3.Row | dict[str, Any], day: date, horizon_days: int = 400) -> date | None:
    """从 `day` 起（含当天）找下一次触发的日期；计划已结束或规则无效时返回 None。

    用于孩子端把「今天不触发但还没结束」的重复任务以「未开始 · 下次 X」的形式提前展示出来。
    """
    if (task["repeat_end"] or "") and task["repeat_end"] < day.isoformat():
        return None
    for offset in range(horizon_days + 1):
        candidate = day + timedelta(days=offset)
        if repeat_matches(task, candidate):
            return candidate
    return None


def ensure_repeat_assignments(conn: sqlite3.Connection, account_id: int | None, day: date | None = None) -> int:
    """把「今天该做的重复任务」物化成已领取(claimed)状态，孩子打开就自动可见。

    只处理当天、不回补历史：漏做的重复任务过期即消失，符合习惯养成语义。
    UNIQUE(task_id, account_id, claim_date) 保证重复调用幂等。
    """
    if account_id is None:
        return 0
    target_day = day or datetime.now().astimezone().date()
    rows = conn.execute("SELECT * FROM tasks WHERE is_active = 1 AND task_type = 'repeat'").fetchall()
    if not rows:
        return 0
    created = 0
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for task in rows:
        if not repeat_matches(task, target_day):
            continue
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO task_assignments(task_id, account_id, status, claim_date, claimed_at)
            VALUES (?, ?, 'claimed', ?, ?)
            """,
            (int(task["id"]), int(account_id), target_day.isoformat(), now),
        )
        created += max(cursor.rowcount, 0)
    return created


def remove_legacy_default_child(conn: sqlite3.Connection) -> None:
    """Remove the untouched child created by versions before 0.6.2."""
    child = conn.execute(
        "SELECT id FROM accounts WHERE username = 'child' AND role = 'child' AND display_name = '小朋友'"
    ).fetchone()
    if child is None:
        return
    child_id = int(child["id"])
    activity = conn.execute(
        """
        SELECT EXISTS(
            SELECT 1 FROM records WHERE account_id = ?
            UNION ALL SELECT 1 FROM point_requests WHERE account_id = ?
            UNION ALL SELECT 1 FROM account_logs WHERE target_id = ? OR actor_id = ?
        )
        """,
        (child_id, child_id, child_id, child_id),
    ).fetchone()[0]
    if activity:
        return
    for table in ("earn_items", "deduct_items", "rewards", "records", "point_requests"):
        conn.execute(f"DELETE FROM {table} WHERE account_id = ?", (child_id,))
    conn.execute("DELETE FROM accounts WHERE id = ?", (child_id,))


def init_db() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'child')),
                avatar TEXT NOT NULL DEFAULT 'boy',
                active INTEGER NOT NULL DEFAULT 1,
                daily_submit_limit INTEGER NOT NULL DEFAULT 10,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS earn_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                points INTEGER NOT NULL CHECK (points > 0),
                icon TEXT NOT NULL DEFAULT 'points.svg'
            );
            CREATE TABLE IF NOT EXISTS deduct_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                points INTEGER NOT NULL CHECK (points > 0),
                icon TEXT NOT NULL DEFAULT 'warning.svg'
            );
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                points INTEGER NOT NULL CHECK (points > 0),
                icon TEXT NOT NULL DEFAULT 'gift.svg'
            );
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS point_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('earn', 'deduct', 'exchange', 'cash_exchange', 'manual')),
                title TEXT NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewer_id INTEGER,
                reject_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS account_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id INTEGER,
                actor_username TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                actor_avatar TEXT NOT NULL DEFAULT 'adult-male',
                target_id INTEGER,
                target_username TEXT NOT NULL,
                target_name TEXT NOT NULL,
                target_role TEXT NOT NULL,
                target_avatar TEXT NOT NULL DEFAULT 'boy',
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '生活',
                task_type TEXT NOT NULL CHECK (task_type IN ('daily', 'epic', 'repeat')),
                difficulty TEXT NOT NULL DEFAULT 'normal' CHECK (difficulty IN ('easy', 'normal', 'hard', 'legendary')),
                reward_coins INTEGER NOT NULL CHECK (reward_coins > 0),
                reward_exp INTEGER NOT NULL CHECK (reward_exp > 0),
                icon TEXT NOT NULL DEFAULT 'points.svg',
                due_date TEXT,
                created_by INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                repeat_freq TEXT,
                repeat_days TEXT,
                repeat_month_week INTEGER,
                repeat_start TEXT,
                repeat_end TEXT
            );
            CREATE TABLE IF NOT EXISTS task_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'claimed' CHECK (status IN ('claimed', 'submitted', 'completed', 'rejected')),
                claim_date TEXT NOT NULL,
                claimed_at TEXT NOT NULL,
                submitted_at TEXT,
                completed_at TEXT,
                reviewer_id INTEGER,
                review_note TEXT,
                UNIQUE(task_id, account_id, claim_date)
            );
            -- 每次「提交审核」都记一条（v0.11.0）。被退回后重新提交也算一次，
            -- 所以不能靠 task_assignments.submitted_at 计数（那会被覆盖）。
            CREATE TABLE IF NOT EXISTS task_submit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                assignment_id INTEGER NOT NULL,
                submit_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_submit_log_account_date
                ON task_submit_log(account_id, submit_date);
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL DEFAULT 'gift.svg',
                requirement_type TEXT NOT NULL,
                requirement_value INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS account_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TEXT NOT NULL,
                UNIQUE(account_id, achievement_id)
            );
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                audience TEXT NOT NULL DEFAULT 'all' CHECK (audience IN ('all', 'children')),
                created_by INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        migrate_point_requests(conn)
        migrate_tasks_repeat(conn)
        if not table_has_column(conn, "accounts", "avatar"):
            conn.execute("ALTER TABLE accounts ADD COLUMN avatar TEXT NOT NULL DEFAULT 'boy'")
        if not table_has_column(conn, "accounts", "daily_submit_limit"):
            # v0.11.0：老库补列，存量孩子账号一律落到默认额度
            conn.execute(
                f"ALTER TABLE accounts ADD COLUMN daily_submit_limit INTEGER NOT NULL DEFAULT {DEFAULT_DAILY_SUBMIT_LIMIT}"
            )
        for column, default in (("actor_avatar", "adult-male"), ("target_avatar", "boy")):
            if not table_has_column(conn, "account_logs", column):
                conn.execute(f"ALTER TABLE account_logs ADD COLUMN {column} TEXT NOT NULL DEFAULT '{default}'")
        for table in ("earn_items", "deduct_items", "rewards", "records", "point_requests"):
            if not table_has_column(conn, table, "account_id"):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN account_id INTEGER")
        for table, default_icon in ITEM_DEFAULT_ICONS.items():
            if not table_has_column(conn, ITEM_TABLES[table], "icon"):
                conn.execute(
                    f"ALTER TABLE {ITEM_TABLES[table]} ADD COLUMN icon TEXT NOT NULL DEFAULT '{default_icon}'"
                )
            for row in conn.execute(f"SELECT id, icon FROM {ITEM_TABLES[table]}").fetchall():
                if not valid_project_icon(row["icon"]):
                    conn.execute(
                        f"UPDATE {ITEM_TABLES[table]} SET icon = ? WHERE id = ?",
                        (default_icon, row["id"]),
                    )
        conn.execute(
            "INSERT OR IGNORE INTO app_settings(key, value, updated_at) VALUES (?, ?, ?)",
            ("points_per_yuan", str(DEFAULT_SETTINGS["points_per_yuan"]), datetime.now().astimezone().isoformat(timespec="seconds")),
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO achievements(
                achievement_key, title, description, icon, requirement_type, requirement_value
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_ACHIEVEMENTS,
        )
        for achievement_key, title, description, icon, requirement_type, requirement_value in DEFAULT_ACHIEVEMENTS:
            conn.execute(
                """
                UPDATE achievements
                SET title = ?, description = ?, icon = ?, requirement_type = ?, requirement_value = ?
                WHERE achievement_key = ?
                """,
                (title, description, icon, requirement_type, requirement_value, achievement_key),
            )

        credentials = admin_credentials_from_env()
        if credentials and not install_credentials_are_applied(credentials):
            if apply_install_admin_credentials(conn, credentials):
                mark_install_credentials_applied(credentials)
        else:
            admin = conn.execute(
                "SELECT * FROM accounts WHERE role = 'admin' AND active = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            if admin is None:
                migrate_legacy_admin_account(conn)
        conn.execute("UPDATE accounts SET avatar = 'adult-male' WHERE username = 'admin' AND avatar = 'boy'")
        remove_legacy_default_child(conn)
        for row in conn.execute("SELECT id FROM accounts WHERE role = 'child' AND active = 1").fetchall():
            seed_items_for_child(conn, int(row["id"]))


def current_date() -> str:
    return datetime.now().astimezone().date().isoformat()


def current_time() -> str:
    return datetime.now().astimezone().strftime("%H:%M")


def valid_date(value: Any) -> str:
    if value in (None, ""):
        return current_date()
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError("日期格式必须为 YYYY-MM-DD") from exc


def positive_int(value: Any, label: str = "积分") -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}必须是整数") from exc
    if number <= 0:
        raise ValueError(f"{label}必须大于 0")
    return number


def points_per_yuan(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM app_settings WHERE key = 'points_per_yuan'").fetchone()
    try:
        rate = int(row["value"]) if row else DEFAULT_SETTINGS["points_per_yuan"]
    except (TypeError, ValueError):
        rate = DEFAULT_SETTINGS["points_per_yuan"]
    return rate if rate > 0 else DEFAULT_SETTINGS["points_per_yuan"]


def adventure_level_key(account_id: int) -> str:
    return f"adventure_level:{int(account_id)}"


def manual_adventure_level(conn: sqlite3.Connection, account_id: int | None) -> int | None:
    if account_id is None:
        return None
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (adventure_level_key(account_id),)).fetchone()
    try:
        level = int(row["value"]) if row else 0
    except (TypeError, ValueError):
        return None
    return level if 1 <= level <= 99 else None


def calculated_adventure_level(conn: sqlite3.Connection, account_id: int | None) -> int:
    if account_id is None:
        return 1
    experience = int(
        conn.execute(
            """
            SELECT COALESCE(SUM(t.reward_exp), 0)
            FROM task_assignments ta
            JOIN tasks t ON t.id = ta.task_id
            WHERE ta.account_id = ? AND ta.status = 'completed'
            """,
            (account_id,),
        ).fetchone()[0]
    )
    return experience // 100 + 1


def adventure_level_for(conn: sqlite3.Connection, account_id: int | None) -> int:
    return manual_adventure_level(conn, account_id) or calculated_adventure_level(conn, account_id)


def adventure_benefits(conn: sqlite3.Connection, account_id: int | None) -> dict[str, Any]:
    level = adventure_level_for(conn, account_id)
    steps = min(max(level - 1, 0), 20)
    earn_bonus_percent = steps * 5
    exchange_discount_percent = steps * 2.5
    return {
        "level": level,
        "earn_bonus_percent": earn_bonus_percent,
        "exchange_discount_percent": exchange_discount_percent,
        "earn_multiplier": 1 + earn_bonus_percent / 100,
        "exchange_multiplier": 1 - exchange_discount_percent / 100,
    }


def adjusted_earn_coins(conn: sqlite3.Connection, account_id: int, coins: int) -> int:
    benefits = adventure_benefits(conn, account_id)
    return max(1, int(math.ceil(coins * benefits["earn_multiplier"])))


def adjusted_exchange_coins(conn: sqlite3.Connection, account_id: int, coins: int) -> int:
    benefits = adventure_benefits(conn, account_id)
    return max(1, int(math.floor(coins * benefits["exchange_multiplier"])))


def settings_payload(conn: sqlite3.Connection, account_id: int | None = None) -> dict[str, Any]:
    manual_level = manual_adventure_level(conn, account_id)
    return {
        "points_per_yuan": points_per_yuan(conn),
        "manual_adventure_level": manual_level,
        "adventure_level_mode": "manual" if manual_level is not None else "auto",
    }


def safe_account(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "role": row["role"],
        "avatar": row["avatar"] or ("adult-male" if row["role"] == "admin" else "boy"),
        "active": bool(row["active"]),
    }


def current_user(conn: sqlite3.Connection) -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = conn.execute("SELECT * FROM accounts WHERE id = ? AND active = 1", (user_id,)).fetchone()
    if user is None:
        session.clear()
    return user


def active_child_id(conn: sqlite3.Connection, user: sqlite3.Row) -> int | None:
    if user["role"] == "child":
        return int(user["id"])
    selected = session.get("selected_child_id")
    if selected:
        child = conn.execute(
            "SELECT id FROM accounts WHERE id = ? AND role = 'child' AND active = 1", (selected,)
        ).fetchone()
        if child:
            return int(child["id"])
    child = conn.execute("SELECT id FROM accounts WHERE role = 'child' AND active = 1 ORDER BY id LIMIT 1").fetchone()
    if child:
        session["selected_child_id"] = int(child["id"])
        return int(child["id"])
    return None


def require_user(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        with connection() as conn:
            user = current_user(conn)
            if user is None:
                return api_error("请先登录", 401)
        return handler(*args, **kwargs)

    return wrapped


def require_admin(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        with connection() as conn:
            user = current_user(conn)
            if user is None:
                return api_error("请先登录", 401)
            if user["role"] != "admin":
                return api_error("只有管理员可以执行此操作", 403)
        return handler(*args, **kwargs)

    return wrapped


def row_item(row: sqlite3.Row, kind: str) -> dict[str, Any]:
    points = int(row["points"])
    if kind == "deduct":
        points = -points
    return {"id": row["id"], "name": row["name"], "points": points, "icon": row["icon"] or ITEM_DEFAULT_ICONS[kind]}


def child_visible_item(row: sqlite3.Row, kind: str, conn: sqlite3.Connection, user: sqlite3.Row) -> dict[str, Any]:
    item = row_item(row, kind)
    if user["role"] != "child":
        return item
    base_points = abs(int(item["points"]))
    if kind == "earn":
        item["base_points"] = base_points
        item["points"] = adjusted_earn_coins(conn, int(user["id"]), base_points)
    elif kind == "reward":
        item["base_points"] = base_points
        item["points"] = adjusted_exchange_coins(conn, int(user["id"]), base_points)
    return item


def get_balance(conn: sqlite3.Connection, account_id: int) -> int:
    return int(
        conn.execute("SELECT COALESCE(SUM(amount), 0) FROM records WHERE account_id = ?", (account_id,)).fetchone()[0]
    )


def request_rows(conn: sqlite3.Connection, user: sqlite3.Row) -> list[dict[str, Any]]:
    if user["role"] == "admin":
        rows = conn.execute(
            """
            SELECT pr.*, a.display_name AS child_name, a.username AS child_username, a.avatar AS child_avatar
            FROM point_requests pr
            JOIN accounts a ON a.id = pr.account_id
            ORDER BY CASE pr.status WHEN 'pending' THEN 0 ELSE 1 END, pr.id DESC
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT pr.*, a.display_name AS child_name, a.username AS child_username, a.avatar AS child_avatar
            FROM point_requests pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE pr.account_id = ?
            ORDER BY pr.id DESC
            """,
            (user["id"],),
        ).fetchall()
    return [dict(row) for row in rows]


def account_overview_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    today = current_date()
    rows = conn.execute(
        """
        SELECT
            a.id, a.username, a.display_name, a.role, a.avatar, a.active, a.created_at,
            COALESCE((SELECT SUM(r.amount) FROM records r WHERE r.account_id = a.id), 0) AS total_points,
            COALESCE((SELECT SUM(r.amount) FROM records r WHERE r.account_id = a.id AND r.date = ?), 0) AS today_net,
            (SELECT COUNT(*) FROM point_requests pr WHERE pr.account_id = a.id AND pr.status = 'pending') AS pending_count,
            (SELECT COUNT(*) FROM task_assignments ta WHERE ta.account_id = a.id AND ta.status = 'submitted') AS task_pending_count,
            COALESCE(a.daily_submit_limit, ?) AS daily_submit_limit,
            (SELECT COUNT(*) FROM task_submit_log tsl WHERE tsl.account_id = a.id AND tsl.submit_date = ?) AS today_submit_count,
            (SELECT MAX(r.created_at) FROM records r WHERE r.account_id = a.id) AS last_activity
        FROM accounts a
        WHERE a.active = 1
        ORDER BY CASE a.role WHEN 'child' THEN 0 ELSE 1 END, a.id
        """,
        (today, DEFAULT_DAILY_SUBMIT_LIMIT, today),
    ).fetchall()
    return [dict(row) for row in rows]


def account_log_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, actor_id, actor_username, actor_name, actor_avatar, target_id, target_username,
               target_name, target_role, target_avatar, action, created_at
        FROM account_logs
        ORDER BY id DESC
        LIMIT 200
        """
    ).fetchall()
    return [dict(row) for row in rows]


def gamification_payload(conn: sqlite3.Connection, account_id: int | None) -> dict[str, Any]:
    if account_id is None:
        return {
            "coins": 0,
            "experience": 0,
            "level": 1,
            "next_level_exp": 100,
            "completed_tasks": 0,
            "unlocked_achievements": 0,
            "level_mode": "auto",
            "earn_bonus_percent": 0,
            "exchange_discount_percent": 0,
        }
    completed_tasks = int(
        conn.execute(
            "SELECT COUNT(*) FROM task_assignments WHERE account_id = ? AND status = 'completed'",
            (account_id,),
        ).fetchone()[0]
    )
    experience = int(
        conn.execute(
            """
            SELECT COALESCE(SUM(t.reward_exp), 0)
            FROM task_assignments ta
            JOIN tasks t ON t.id = ta.task_id
            WHERE ta.account_id = ? AND ta.status = 'completed'
            """,
            (account_id,),
        ).fetchone()[0]
    )
    unlocked = int(
        conn.execute(
            "SELECT COUNT(*) FROM account_achievements WHERE account_id = ?",
            (account_id,),
        ).fetchone()[0]
    )
    benefits = adventure_benefits(conn, account_id)
    level = benefits["level"]
    return {
        "coins": get_balance(conn, account_id),
        "experience": experience,
        "level": level,
        "next_level_exp": level * 100,
        "completed_tasks": completed_tasks,
        "unlocked_achievements": unlocked,
        "level_mode": "manual" if manual_adventure_level(conn, account_id) is not None else "auto",
        "earn_bonus_percent": benefits["earn_bonus_percent"],
        "exchange_discount_percent": benefits["exchange_discount_percent"],
    }


def achievement_rows(conn: sqlite3.Connection, account_id: int | None) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT a.id, a.achievement_key, a.title, a.description, a.icon,
               a.requirement_type, a.requirement_value,
               aa.unlocked_at
        FROM achievements a
        LEFT JOIN account_achievements aa
          ON aa.achievement_id = a.id AND aa.account_id = ?
        ORDER BY CASE WHEN aa.unlocked_at IS NULL THEN 1 ELSE 0 END, a.id
        """,
        (account_id or 0,),
    ).fetchall()
    return [
        {
            **dict(row),
            "unlocked": row["unlocked_at"] is not None,
        }
        for row in rows
    ]


def task_assignment_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "account_id": row["account_id"],
        "account_name": row["account_name"],
        "account_avatar": row["account_avatar"],
        "status": row["status"],
        "claim_date": row["claim_date"],
        "claimed_at": row["claimed_at"],
        "submitted_at": row["submitted_at"],
        "completed_at": row["completed_at"],
        "review_note": row["review_note"],
    }


def daily_submit_limit_for(conn: sqlite3.Connection, account_id: int | None) -> int:
    """孩子的每日提交审核额度；0 表示不限制。缺列/缺行/脏数据一律回落到默认值。"""
    if account_id is None:
        return DEFAULT_DAILY_SUBMIT_LIMIT
    row = conn.execute("SELECT daily_submit_limit FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None or row["daily_submit_limit"] is None:
        return DEFAULT_DAILY_SUBMIT_LIMIT
    try:
        limit = int(row["daily_submit_limit"])
    except (TypeError, ValueError):
        return DEFAULT_DAILY_SUBMIT_LIMIT
    if limit < 0:
        return DEFAULT_DAILY_SUBMIT_LIMIT
    return min(limit, MAX_DAILY_SUBMIT_LIMIT)


def submit_count_today(conn: sqlite3.Connection, account_id: int | None, day: str | None = None) -> int:
    """当天已经点了几次「提交审核」。被退回后重新提交也计数，所以查的是事件日志。"""
    if account_id is None:
        return 0
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM task_submit_log WHERE account_id = ? AND submit_date = ?",
            (account_id, day or current_date()),
        ).fetchone()[0]
    )


def submit_quota_payload(conn: sqlite3.Connection, account_id: int | None) -> dict[str, Any]:
    """给前端展示用的额度快照；limit=0 时 remaining 为 None（表示不限制）。"""
    limit = daily_submit_limit_for(conn, account_id)
    used = submit_count_today(conn, account_id)
    return {
        "limit": limit,
        "used": used,
        "unlimited": limit == 0,
        "remaining": None if limit == 0 else max(limit - used, 0),
    }


def normalize_submit_limit(raw: Any) -> int:
    """校验账号级「每日提交上限」：0 = 不限制，1..999 为具体次数。"""
    if raw is None or str(raw).strip() == "":
        return DEFAULT_DAILY_SUBMIT_LIMIT
    try:
        limit = int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("每日提交上限必须是 0 到 999 的整数") from exc
    if limit < 0 or limit > MAX_DAILY_SUBMIT_LIMIT:
        raise ValueError(f"每日提交上限必须在 0 到 {MAX_DAILY_SUBMIT_LIMIT} 之间（0 表示不限制）")
    return limit


def task_is_edit_locked(task_type: str, approved_count: int) -> bool:
    """任务是否已「锁定不可编辑」：非重复任务一旦有审核通过的提交，规则就已生效。

    - 已完成并验收通过的日常/史诗任务：再改标题或奖励等于篡改已结算的结果，管理端只能查看。
    - 重复任务是长期模板，孩子每周都会重新做一次，因此永远允许修改规则。
    """
    return task_type != "repeat" and approved_count > 0


def task_rows(conn: sqlite3.Connection, user: sqlite3.Row) -> list[dict[str, Any]]:
    is_child = user["role"] == "child"
    target_account = int(user["id"]) if is_child else active_child_id(conn, user)
    # 重复任务：先把「今天该做的」落成已领取状态，孩子打开就能直接看到，无需每天手动创建
    ensure_repeat_assignments(conn, target_account)
    today = datetime.now().astimezone().date()
    tasks = conn.execute(
        """
        SELECT t.*, a.display_name AS creator_name
        FROM tasks t
        LEFT JOIN accounts a ON a.id = t.created_by
        WHERE t.is_active = 1
        ORDER BY CASE t.task_type WHEN 'epic' THEN 0 WHEN 'repeat' THEN 1 ELSE 2 END, t.id DESC
        """
    ).fetchall()
    result: list[dict[str, Any]] = []
    for task in tasks:
        is_repeat = task["task_type"] == "repeat"
        active_today = repeat_matches(task, today) if is_repeat else True
        # 重复任务：算出下一次触发日期；只有「计划已结束/规则无效」才对孩子彻底隐藏。
        # 今天不触发但还没结束的，孩子端以「未开始 · 下次 X」提前展示（漏做仍不补做）。
        next_day = next_repeat_occurrence(task, today) if is_repeat else None
        if is_child and is_repeat and next_day is None:
            continue
        assignments = conn.execute(
            """
            SELECT ta.*, a.display_name AS account_name, a.avatar AS account_avatar
            FROM task_assignments ta
            JOIN accounts a ON a.id = ta.account_id
            WHERE ta.task_id = ?
            ORDER BY ta.id DESC
            """,
            (task["id"],),
        ).fetchall()
        own = next(
            (row for row in assignments if target_account is not None and int(row["account_id"]) == int(target_account)),
            None,
        )
        approved_count = sum(1 for row in assignments if row["status"] == "completed")
        result.append(
            {
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "category": task["category"],
                "task_type": task["task_type"],
                "difficulty": task["difficulty"],
                "reward_coins": adjusted_earn_coins(conn, int(user["id"]), int(task["reward_coins"])) if is_child else task["reward_coins"],
                "base_reward_coins": task["reward_coins"],
                "reward_exp": task["reward_exp"],
                "icon": task["icon"],
                "due_date": task["due_date"],
                "creator_name": task["creator_name"] or "管理员",
                "participant_count": len(assignments),
                "approved_count": approved_count,
                # v0.13.2：验收通过后管理端不能再编辑（后端 PUT 同样会拒绝）
                "edit_locked": task_is_edit_locked(task["task_type"], approved_count),
                "assignments": [task_assignment_row(row) for row in assignments] if not is_child else [],
                "my_assignment": task_assignment_row(own) if own is not None else None,
                "repeat_freq": task["repeat_freq"],
                "repeat_days": parse_weekday_list(task["repeat_days"]) if is_repeat else [],
                "repeat_month_week": task["repeat_month_week"],
                "repeat_start": task["repeat_start"],
                "repeat_end": task["repeat_end"],
                "repeat_text": repeat_rule_text(task),
                "active_today": active_today,
                "next_date": next_day.isoformat() if next_day else None,
            }
        )
    if is_child:
        # 今天能做的排在前面，未来才开始的排在后面（sort 稳定，同组保持原有类型顺序）
        result.sort(key=lambda item: 0 if item["active_today"] else 1)
    return result


def task_review_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """管理端「审核中心」的任务验收队列：所有孩子已提交、等待验收的任务。

    刻意**不过滤** `tasks.is_active`：任务被撤下（软删除）后，孩子已经提交的那一份
    仍需要管理端给出结论，否则会永远卡在「待验收」而既拿不到积分也无法重做。
    """
    rows = conn.execute(
        """
        SELECT ta.id AS assignment_id, ta.task_id, ta.account_id, ta.claim_date, ta.submitted_at,
               t.title AS task_title, t.icon AS task_icon, t.is_active AS task_active,
               t.reward_coins AS base_reward_coins, t.reward_exp AS reward_exp,
               a.display_name AS child_name, a.avatar AS child_avatar
        FROM task_assignments ta
        JOIN tasks t ON t.id = ta.task_id
        JOIN accounts a ON a.id = ta.account_id
        WHERE ta.status = 'submitted'
        ORDER BY ta.id DESC
        """
    ).fetchall()
    return [
        {
            "assignment_id": row["assignment_id"],
            "task_id": row["task_id"],
            "account_id": row["account_id"],
            "child_name": row["child_name"],
            "child_avatar": row["child_avatar"],
            "task_title": row["task_title"],
            "task_icon": row["task_icon"],
            "task_active": bool(row["task_active"]),
            "claim_date": row["claim_date"],
            "submitted_at": row["submitted_at"],
            "reward_coins": adjusted_earn_coins(conn, int(row["account_id"]), int(row["base_reward_coins"])),
            "base_reward_coins": int(row["base_reward_coins"]),
            "reward_exp": int(row["reward_exp"] or 0),
        }
        for row in rows
    ]


def announcement_rows(conn: sqlite3.Connection, user: sqlite3.Row) -> list[dict[str, Any]]:
    if user["role"] == "admin":
        rows = conn.execute(
            "SELECT * FROM announcements WHERE is_active = 1 ORDER BY id DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM announcements WHERE is_active = 1 AND audience IN ('all', 'children') ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def unlock_achievements(conn: sqlite3.Connection, account_id: int) -> None:
    completed_tasks = int(
        conn.execute(
            "SELECT COUNT(*) FROM task_assignments WHERE account_id = ? AND status = 'completed'",
            (account_id,),
        ).fetchone()[0]
    )
    epic_tasks = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM task_assignments ta
            JOIN tasks t ON t.id = ta.task_id
            WHERE ta.account_id = ? AND ta.status = 'completed' AND t.task_type = 'epic'
            """,
            (account_id,),
        ).fetchone()[0]
    )
    earned_coins = int(
        conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM records WHERE account_id = ? AND amount > 0",
            (account_id,),
        ).fetchone()[0]
    )
    daily_tasks = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM task_assignments ta
            JOIN tasks t ON t.id = ta.task_id
            WHERE ta.account_id = ? AND ta.status = 'completed' AND t.task_type IN ('daily', 'repeat')
            """,
            (account_id,),
        ).fetchone()[0]
    )
    progress = {
        "completed_tasks": completed_tasks,
        "epic_tasks": epic_tasks,
        "earned_coins": earned_coins,
        "daily_tasks": daily_tasks,
    }
    definitions = conn.execute("SELECT * FROM achievements").fetchall()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for achievement in definitions:
        if progress.get(achievement["requirement_type"], 0) < achievement["requirement_value"]:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO account_achievements(account_id, achievement_id, unlocked_at) VALUES (?, ?, ?)",
            (account_id, achievement["id"], now),
        )


def state_payload(conn: sqlite3.Connection, user: sqlite3.Row) -> dict[str, Any]:
    account_id = active_child_id(conn, user)
    if account_id is None:
        return {
            "version": APP_VERSION,
            "settings": settings_payload(conn, None),
            "user": safe_account(user),
            "children": [],
            "active_child": None,
            "active_child_id": None,
            "total_points": 0,
            "earn_items": [],
            "deduct_items": [],
            "rewards": [],
            "records": [],
            "requests": request_rows(conn, user),
            "task_reviews": task_review_rows(conn) if user["role"] == "admin" else [],
            "tasks": task_rows(conn, user),
            "submit_quota": submit_quota_payload(conn, None),
            "announcements": announcement_rows(conn, user),
            "achievements": achievement_rows(conn, None),
            "gamification": gamification_payload(conn, None),
            "account_overview": account_overview_rows(conn) if user["role"] == "admin" else [],
            "account_logs": account_log_rows(conn) if user["role"] == "admin" else [],
            "permissions": {
                "can_manage_points": user["role"] == "admin",
                "can_manage_accounts": user["role"] == "admin",
                "can_request_earn": user["role"] == "child",
                "can_request_exchange": user["role"] == "child",
            },
        }
    active_child = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    earn = conn.execute("SELECT id, name, points, icon FROM earn_items WHERE account_id = ? ORDER BY id", (account_id,)).fetchall()
    deduct = conn.execute("SELECT id, name, points, icon FROM deduct_items WHERE account_id = ? ORDER BY id", (account_id,)).fetchall()
    rewards = conn.execute("SELECT id, name, points, icon FROM rewards WHERE account_id = ? ORDER BY id", (account_id,)).fetchall()
    records = conn.execute(
        "SELECT id, title, amount, type, date, time FROM records WHERE account_id = ? ORDER BY id DESC", (account_id,)
    ).fetchall()
    children = conn.execute("SELECT * FROM accounts WHERE role = 'child' AND active = 1 ORDER BY id").fetchall()
    return {
        "version": APP_VERSION,
        "settings": settings_payload(conn, account_id),
        "user": safe_account(user),
        "children": [safe_account(row) for row in children],
        "active_child": safe_account(active_child),
        "active_child_id": account_id,
        "total_points": get_balance(conn, account_id),
        "earn_items": [child_visible_item(row, "earn", conn, user) for row in earn],
        "deduct_items": [row_item(row, "deduct") for row in deduct],
        "rewards": [child_visible_item(row, "reward", conn, user) for row in rewards],
        "records": [dict(row) for row in records],
        "requests": request_rows(conn, user),
        "task_reviews": task_review_rows(conn) if user["role"] == "admin" else [],
        "tasks": task_rows(conn, user),
        "submit_quota": submit_quota_payload(conn, account_id),
        "announcements": announcement_rows(conn, user),
        "achievements": achievement_rows(conn, account_id),
        "gamification": gamification_payload(conn, account_id),
        "account_overview": account_overview_rows(conn) if user["role"] == "admin" else [],
        "account_logs": account_log_rows(conn) if user["role"] == "admin" else [],
        "permissions": {
            "can_manage_points": user["role"] == "admin",
            "can_manage_accounts": user["role"] == "admin",
            "can_request_earn": user["role"] == "child",
            "can_request_exchange": user["role"] == "child",
        },
    }


def api_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def find_custom_asset(asset_key: str) -> Path | None:
    """Find a user image whether it is flat or nested by an upload tool."""
    if asset_key not in CUSTOM_ASSET_KEYS:
        return None
    custom_dir = RESOURCE_DIR / "static" / "custom"
    for entry in sorted(custom_dir.glob(f"{asset_key}.*"), key=lambda item: item.name.lower()):
        if entry.is_file() and entry.suffix.lower() in CUSTOM_IMAGE_SUFFIXES:
            return entry
        if entry.is_dir():
            nested = sorted(
                (child for child in entry.rglob("*") if child.is_file() and child.suffix.lower() in CUSTOM_IMAGE_SUFFIXES),
                key=lambda item: str(item).lower(),
            )
            if nested:
                return nested[0]
    return None


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(os.getenv("COOKIE_SECURE", "") or "").lower() in ("1", "true", "yes"),
)


# --- 登录限流（防止暴力破解） ---
LOGIN_ATTEMPTS: dict[str, list[float]] = {}
LOGIN_LOCK = Lock()
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300


def login_rate_limited(remote_addr: str) -> bool:
    now = time.time()
    with LOGIN_LOCK:
        attempts = LOGIN_ATTEMPTS.get(remote_addr, [])
        attempts = [stamp for stamp in attempts if now - stamp < LOGIN_WINDOW_SECONDS]
        LOGIN_ATTEMPTS[remote_addr] = attempts
        return len(attempts) >= MAX_LOGIN_ATTEMPTS


def record_failed_login(remote_addr: str) -> None:
    now = time.time()
    with LOGIN_LOCK:
        LOGIN_ATTEMPTS.setdefault(remote_addr, []).append(now)


def clear_failed_logins(remote_addr: str) -> None:
    with LOGIN_LOCK:
        LOGIN_ATTEMPTS.pop(remote_addr, None)


@app.get("/custom-assets/<asset_key>")
def custom_asset(asset_key: str):
    asset = find_custom_asset(asset_key)
    if asset is None:
        abort(404)
    return send_file(asset)


@app.get("/")
def index():
    return render_template("index.html", app_version=APP_VERSION)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "version": APP_VERSION})


# ---- 备份 / 覆盖式导入（v0.13.0）----
# 导出与导入共用同一份表清单：漏掉 task_submit_log 会让「今日已提交次数」恢复后归零。
EXPORT_TABLES = [
    "accounts", "earn_items", "deduct_items", "rewards", "records",
    "point_requests", "account_logs", "app_settings", "tasks",
    "task_assignments", "task_submit_log", "achievements",
    "account_achievements", "announcements",
]
# 覆盖式导入的清空顺序：先子表后主表（本库没声明外键，这里只是保险）。
IMPORT_CLEAR_ORDER = [
    "task_submit_log", "account_achievements", "task_assignments", "records",
    "point_requests", "account_logs", "achievements", "announcements",
    "tasks", "app_settings", "earn_items", "deduct_items", "rewards", "accounts",
]
MAX_IMPORT_BYTES = 25 * 1024 * 1024


def collect_export_payload() -> dict:
    with connection() as conn:
        data = {
            table: [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]
            for table in EXPORT_TABLES
        }
    return {
        "version": APP_VERSION,
        "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "data": data,
    }


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def write_backup_snapshot() -> str | None:
    """导入前把当前整库另存一份到 data/backups，导入失败或后悔时能找回来。"""
    try:
        folder = DATA_DIR / "backups"
        folder.mkdir(parents=True, exist_ok=True)
        # 加随机后缀：同一秒内连续导入不会把上一份备份覆盖掉
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = folder / f"pre-import-{stamp}-{secrets.token_hex(2)}.json"
        path.write_text(json.dumps(collect_export_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
    except OSError:
        return None


@app.get("/api/export")
@require_admin
def export_family_data():
    return jsonify(collect_export_payload())


@app.post("/api/import")
@require_admin
def import_family_data():
    """覆盖式导入：整库替换为备份文件内容（导入前自动另存一份当前数据）。"""
    payload = request.get_json(silent=True)
    if payload is None:
        raw = request.get_data(cache=True)
        if not raw:
            return api_error("没有收到导入文件")
        if len(raw) > MAX_IMPORT_BYTES:
            return api_error("导入文件过大（上限 25MB）")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return api_error("导入文件不是有效的 JSON")
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict) or not data:
        return api_error("文件格式不对：缺少 data 数据表")
    unknown = [table for table in data if table not in EXPORT_TABLES]
    if unknown:
        return api_error(f"导入文件含未知数据表：{', '.join(unknown[:5])}")
    for table, rows in data.items():
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            return api_error(f"{table} 的格式不对，应该是一组记录")

    with connection() as conn:
        user = current_user(conn)
    admin_id = user["id"] if user else None
    backup = write_backup_snapshot()
    try:
        with connection() as conn:
            for table in IMPORT_CLEAR_ORDER:
                conn.execute(f"DELETE FROM {table}")
            inserted = {}
            for table in EXPORT_TABLES:
                rows = data.get(table) or []
                if not rows:
                    continue
                # 只写当前版本真实存在的列：老版本备份缺列、多列都不会整库失败
                columns = [name for name in table_columns(conn, table) if name in rows[0]]
                if not columns:
                    continue
                placeholders = ",".join(["?"] * len(columns))
                sql = f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                conn.executemany(sql, [tuple(row.get(name) for name in columns) for row in rows])
                inserted[table] = len(rows)
    except sqlite3.Error as exc:
        # connection() 会整段回滚，导入失败时数据库保持原样
        return api_error(f"导入失败，数据已保持原样（{exc}）")

    with connection() as conn:
        still_admin = conn.execute(
            "SELECT id FROM accounts WHERE id = ? AND role = 'admin'", (admin_id,)
        ).fetchone() if admin_id else None
        if admin_id and not still_admin:
            # 导入的是别处的数据，当前登录的管理账号已不存在，必须重新登录
            session.clear()
            return jsonify({"imported": True, "relogin": True, "backup": backup, "tables": inserted})
        return jsonify({
            "imported": True,
            "relogin": False,
            "backup": backup,
            "tables": inserted,
            "state": state_payload(conn, current_user(conn)),
        })


@app.get("/api/setup/status")
def setup_status():
    with connection() as conn:
        configured = conn.execute(
            "SELECT 1 FROM accounts WHERE role = 'admin' AND active = 1 LIMIT 1"
        ).fetchone() is not None
    return jsonify({"configured": configured})


@app.post("/api/setup/admin")
def setup_admin():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    password_confirm = str(payload.get("password_confirm", ""))
    if not USERNAME_PATTERN.fullmatch(username):
        return api_error("管理员账号需为 3-32 位字母、数字、下划线、点或短横线")
    if len(password) < 6:
        return api_error("管理员密码至少需要 6 位")
    if password != password_confirm:
        return api_error("两次输入的密码不一致")
    with connection() as conn:
        existing = conn.execute(
            "SELECT 1 FROM accounts WHERE role = 'admin' AND active = 1 LIMIT 1"
        ).fetchone()
        if existing is not None:
            return api_error("管理员已经设置完成，请直接登录", 409)
        try:
            user = create_admin_account(conn, username, password)
        except sqlite3.IntegrityError:
            return api_error("账号名已存在")
        session.clear()
        session["user_id"] = int(user["id"])
        return jsonify(state_payload(conn, user)), 201


@app.post("/api/auth/login")
def login():
    remote = request.remote_addr or "unknown"
    if login_rate_limited(remote):
        return api_error("登录尝试过于频繁，请稍后再试", 429)
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    with connection() as conn:
        user = conn.execute("SELECT * FROM accounts WHERE username = ? AND active = 1", (username,)).fetchone()
        if user is None or not password_matches(password, user["password_hash"]):
            record_failed_login(remote)
            return api_error("账号或密码错误", 401)
        session.clear()
        session["user_id"] = int(user["id"])
        clear_failed_logins(remote)
        if user["role"] == "admin":
            first_child = conn.execute("SELECT id FROM accounts WHERE role = 'child' AND active = 1 ORDER BY id LIMIT 1").fetchone()
            if first_child:
                session["selected_child_id"] = int(first_child["id"])
        else:
            session["selected_child_id"] = int(user["id"])
        return jsonify(state_payload(conn, user))


@app.post("/api/auth/register-child")
def register_child():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    display_name = str(payload.get("display_name", "")).strip()
    password = str(payload.get("password", ""))
    password_confirm = str(payload.get("password_confirm", ""))
    avatar = str(payload.get("avatar") or "boy")
    if not USERNAME_PATTERN.fullmatch(username):
        return api_error("孩子账号需为 3-32 位字母、数字、下划线、点或短横线")
    if len(password) < 6:
        return api_error("孩子密码至少需要 6 位")
    if password != password_confirm:
        return api_error("两次输入的密码不一致")
    if avatar not in CHILD_AVATARS:
        return api_error("孩子头像类型无效")
    if not display_name:
        display_name = username
    with connection() as conn:
        admin = conn.execute(
            "SELECT 1 FROM accounts WHERE role = 'admin' AND active = 1 LIMIT 1"
        ).fetchone()
        if admin is None:
            return api_error("请先完成管理员首次设置", 409)
        try:
            cursor = conn.execute(
                "INSERT INTO accounts(username, password_hash, display_name, role, avatar, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    username,
                    password_hash(password),
                    display_name,
                    "child",
                    avatar,
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )
        except sqlite3.IntegrityError:
            return api_error("账号名已存在")
        seed_items_for_child(conn, int(cursor.lastrowid))
        user = conn.execute("SELECT * FROM accounts WHERE id = ?", (cursor.lastrowid,)).fetchone()
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO account_logs(
                actor_id, actor_username, actor_name, actor_avatar, target_id, target_username,
                target_name, target_role, target_avatar, action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["username"],
                user["display_name"],
                user["avatar"],
                user["id"],
                user["username"],
                user["display_name"],
                user["role"],
                user["avatar"],
                "register_child",
                now,
            ),
        )
        session.clear()
        session["user_id"] = int(user["id"])
        session["selected_child_id"] = int(user["id"])
        return jsonify(state_payload(conn, user)), 201


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.put("/api/auth/password")
@require_user
def change_own_password():
    payload = request.get_json(silent=True) or {}
    current_password = str(payload.get("current_password", ""))
    new_password = str(payload.get("password", ""))
    password_confirm = str(payload.get("password_confirm", ""))
    if len(new_password) < 6:
        return api_error("新密码至少需要 6 位")
    if new_password != password_confirm:
        return api_error("两次输入的新密码不一致")
    with connection() as conn:
        user = current_user(conn)
        if user is None:
            return api_error("请先登录", 401)
        if user["role"] != "child":
            return api_error("管理账号请在账号管理中修改密码", 403)
        if not password_matches(current_password, user["password_hash"]):
            return api_error("当前密码错误", 401)
        conn.execute(
            "UPDATE accounts SET password_hash = ? WHERE id = ?",
            (password_hash(new_password), user["id"]),
        )
        conn.execute(
            """
            INSERT INTO account_logs(
                actor_id, actor_username, actor_name, actor_avatar, target_id, target_username,
                target_name, target_role, target_avatar, action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], user["username"], user["display_name"], user["avatar"],
                user["id"], user["username"], user["display_name"], user["role"], user["avatar"],
                "change_password", datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
        return jsonify({"ok": True})


@app.get("/api/auth/me")
def auth_me():
    with connection() as conn:
        user = current_user(conn)
        if user is None:
            return jsonify({"authenticated": False}), 401
        return jsonify({"authenticated": True, "user": safe_account(user)})


@app.post("/api/auth/select-child")
@require_admin
def select_child():
    payload = request.get_json(silent=True) or {}
    try:
        child_id = int(payload.get("child_id"))
    except (TypeError, ValueError):
        return api_error("孩子账号无效")
    with connection() as conn:
        user = current_user(conn)
        child = conn.execute("SELECT * FROM accounts WHERE id = ? AND role = 'child' AND active = 1", (child_id,)).fetchone()
        if user is None or child is None:
            return api_error("孩子账号不存在", 404)
        session["selected_child_id"] = child_id
        return jsonify(state_payload(conn, user))


@app.get("/api/accounts")
@require_admin
def list_accounts():
    with connection() as conn:
        return jsonify({"accounts": [safe_account(row) for row in conn.execute("SELECT * FROM accounts ORDER BY role, id").fetchall()]})


@app.post("/api/accounts")
@require_admin
def create_account():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    display_name = str(payload.get("display_name", "")).strip()
    password = str(payload.get("password", ""))
    role = str(payload.get("role", "child")).lower()
    avatar = str(payload.get("avatar") or ("adult-male" if role == "admin" else "boy"))
    if not USERNAME_PATTERN.fullmatch(username):
        return api_error("账号需为 3-32 位字母、数字、下划线、点或短横线")
    if len(password) < 6:
        return api_error("密码至少需要 6 位")
    if role not in ("admin", "child"):
        return api_error("账号类型无效")
    if avatar not in AVATAR_OPTIONS or (role == "child" and avatar not in CHILD_AVATARS):
        return api_error("头像类型无效")
    if not display_name:
        display_name = username
    try:
        daily_submit_limit = normalize_submit_limit(payload.get("daily_submit_limit"))
    except ValueError as exc:
        return api_error(str(exc))
    with connection() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO accounts(username, password_hash, display_name, role, avatar, daily_submit_limit, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, password_hash(password), display_name, role, avatar, daily_submit_limit, datetime.now().astimezone().isoformat(timespec="seconds")),
            )
        except sqlite3.IntegrityError:
            return api_error("账号名已存在")
        if role == "child":
            seed_items_for_child(conn, int(cursor.lastrowid))
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (cursor.lastrowid,)).fetchone()
        actor = current_user(conn)
        conn.execute(
            """
            INSERT INTO account_logs(
                actor_id, actor_username, actor_name, actor_avatar, target_id, target_username,
                target_name, target_role, target_avatar, action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                actor["id"],
                actor["username"],
                actor["display_name"],
                actor["avatar"],
                row["id"],
                row["username"],
                row["display_name"],
                row["role"],
                row["avatar"],
                "create_child" if role == "child" else "create_admin",
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
        return jsonify(safe_account(row)), 201


@app.delete("/api/accounts/<int:account_id>")
@require_admin
def delete_account(account_id: int):
    with connection() as conn:
        user = current_user(conn)
        target = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if user is None or target is None:
            return api_error("账号不存在", 404)
        if int(user["id"]) == account_id:
            return api_error("不能删除当前登录账号")
        if target["role"] == "admin" and conn.execute("SELECT COUNT(*) FROM accounts WHERE role = 'admin' AND active = 1").fetchone()[0] <= 1:
            return api_error("至少需要保留一个管理员账号")
        conn.execute(
            """
            INSERT INTO account_logs(
                actor_id, actor_username, actor_name, actor_avatar, target_id, target_username,
                target_name, target_role, target_avatar, action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["username"],
                user["display_name"],
                user["avatar"],
                target["id"],
                target["username"],
                target["display_name"],
                target["role"],
                target["avatar"],
                "delete_child" if target["role"] == "child" else "delete_admin",
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
        for table in ("earn_items", "deduct_items", "rewards", "records", "point_requests", "task_assignments", "task_submit_log", "account_achievements"):
            conn.execute(f"DELETE FROM {table} WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM app_settings WHERE key = ?", (adventure_level_key(account_id),))
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        if session.get("selected_child_id") == account_id:
            session.pop("selected_child_id", None)
        return jsonify({"deleted": True})


@app.route("/api/accounts/<int:account_id>", methods=["PUT", "PATCH"])
@require_admin
def update_account(account_id: int):
    payload = request.get_json(silent=True) or {}
    display_name = str(payload.get("display_name", "")).strip()
    password = str(payload.get("password", ""))
    avatar = str(payload.get("avatar", ""))
    if not display_name:
        return api_error("显示名称不能为空")
    if password and len(password) < 6:
        return api_error("密码至少需要 6 位")
    submit_limit = None
    if payload.get("daily_submit_limit") is not None:
        try:
            submit_limit = normalize_submit_limit(payload.get("daily_submit_limit"))
        except ValueError as exc:
            return api_error(str(exc))
    with connection() as conn:
        user = current_user(conn)
        target = conn.execute("SELECT * FROM accounts WHERE id = ? AND active = 1", (account_id,)).fetchone()
        if user is None or target is None:
            return api_error("账号不存在", 404)
        allowed_avatars = CHILD_AVATARS if target["role"] == "child" else {"adult-male", "adult-female"}
        if not avatar:
            avatar = target["avatar"]
        if avatar not in allowed_avatars:
            return api_error("头像类型无效")
        assignments = ["display_name = ?", "avatar = ?"]
        values: list[Any] = [display_name, avatar]
        if password:
            assignments.append("password_hash = ?")
            values.append(password_hash(password))
        if submit_limit is not None and target["role"] == "child":
            assignments.append("daily_submit_limit = ?")
            values.append(submit_limit)
        values.append(account_id)
        conn.execute(f"UPDATE accounts SET {', '.join(assignments)} WHERE id = ?", values)
        target = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        conn.execute(
            """
            INSERT INTO account_logs(
                actor_id, actor_username, actor_name, actor_avatar, target_id, target_username,
                target_name, target_role, target_avatar, action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], user["username"], user["display_name"], user["avatar"],
                target["id"], target["username"], target["display_name"], target["role"], target["avatar"],
                "update_child" if target["role"] == "child" else "update_admin",
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
        return jsonify(safe_account(target))


@app.get("/api/state")
@require_user
def get_state():
    with connection() as conn:
        user = current_user(conn)
        return jsonify(state_payload(conn, user))


@app.route("/api/settings", methods=["PUT", "PATCH"])
@require_admin
def update_settings():
    payload = request.get_json(silent=True) or {}
    rate = None
    if "points_per_yuan" in payload:
        try:
            rate = positive_int(payload.get("points_per_yuan"), "换算比例")
        except ValueError as exc:
            return api_error(str(exc))
        if rate > 1_000_000:
            return api_error("换算比例不能超过 1000000")
    if rate is None and "adventure_level" not in payload:
        return api_error("没有需要保存的设置")
    with connection() as conn:
        user = current_user(conn)
        account_id = active_child_id(conn, user)
        if "adventure_level" in payload:
            requested_level = str(payload.get("adventure_level") or "").strip().lower()
            level_key = adventure_level_key(account_id) if account_id is not None else None
            if requested_level in ("", "auto"):
                if level_key:
                    conn.execute("DELETE FROM app_settings WHERE key = ?", (level_key,))
            else:
                try:
                    level = int(requested_level)
                except ValueError:
                    return api_error("冒险等级必须是 1 到 99 的整数，或选择自动计算")
                if not 1 <= level <= 99:
                    return api_error("冒险等级必须在 1 到 99 之间")
                if level_key is None:
                    return api_error("请先创建并选择孩子账号")
                conn.execute(
                    """
                    INSERT INTO app_settings(key, value, updated_at) VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                    """,
                    (level_key, str(level), datetime.now().astimezone().isoformat(timespec="seconds")),
                )
        if rate is not None:
            now = datetime.now().astimezone().isoformat(timespec="seconds")
            updated = conn.execute(
                "UPDATE app_settings SET value = ?, updated_at = ? WHERE key = 'points_per_yuan'",
                (str(rate), now),
            )
            if updated.rowcount == 0:
                conn.execute(
                    "INSERT INTO app_settings(key, value, updated_at) VALUES (?, ?, ?)",
                    ("points_per_yuan", str(rate), now),
                )
        return jsonify(state_payload(conn, user))


@app.get("/api/tasks")
@require_user
def list_tasks():
    with connection() as conn:
        user = current_user(conn)
        account_id = int(user["id"]) if user["role"] == "child" else active_child_id(conn, user)
        return jsonify(
            {
                "tasks": task_rows(conn, user),
                "achievements": achievement_rows(conn, account_id),
                "gamification": gamification_payload(conn, account_id),
            }
        )


@app.post("/api/tasks")
@require_admin
def create_task():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()[:80]
    description = str(payload.get("description", "")).strip()[:240]
    category = str(payload.get("category", "生活")).strip()[:30] or "生活"
    task_type = str(payload.get("task_type", "daily")).lower()
    difficulty = str(payload.get("difficulty", "normal")).lower()
    icon = str(payload.get("icon") or "points.svg")
    due_date_value = str(payload.get("due_date") or "").strip()
    try:
        reward_coins = positive_int(payload.get("reward_coins"), "积分奖励")
        reward_exp = positive_int(payload.get("reward_exp"), "经验奖励")
        due_date = valid_date(due_date_value) if due_date_value else None
        repeat_rule = normalize_repeat_rule(payload, task_type)
    except ValueError as exc:
        return api_error(str(exc))
    if not title:
        return api_error("任务标题不能为空")
    if task_type not in TASK_TYPES:
        return api_error("任务类型无效")
    if difficulty not in TASK_DIFFICULTIES:
        return api_error("任务难度无效")
    if not valid_project_icon(icon):
        return api_error("任务图标无效")
    with connection() as conn:
        user = current_user(conn)
        cursor = conn.execute(
            """
            INSERT INTO tasks(
                title, description, category, task_type, difficulty,
                reward_coins, reward_exp, icon, due_date, created_by, created_at,
                repeat_freq, repeat_days, repeat_month_week, repeat_start, repeat_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                category,
                task_type,
                difficulty,
                reward_coins,
                reward_exp,
                icon,
                due_date,
                user["id"],
                datetime.now().astimezone().isoformat(timespec="seconds"),
                repeat_rule["repeat_freq"],
                repeat_rule["repeat_days"],
                repeat_rule["repeat_month_week"],
                repeat_rule["repeat_start"],
                repeat_rule["repeat_end"],
            ),
        )
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify({"task": dict(task), "state": state_payload(conn, user)}), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT", "DELETE"])
@require_admin
def task_detail(task_id: int):
    with connection() as conn:
        user = current_user(conn)
        task = conn.execute("SELECT * FROM tasks WHERE id = ? AND is_active = 1", (task_id,)).fetchone()
        if task is None:
            return api_error("任务不存在", 404)
        if request.method == "DELETE":
            conn.execute("UPDATE tasks SET is_active = 0 WHERE id = ?", (task_id,))
            return jsonify({"deleted": True})
        # v0.13.2：任务已有审核通过的提交 → 规则已生效，禁止再编辑（前端同时隐藏「编辑」按钮）
        approved = conn.execute(
            "SELECT COUNT(*) AS total FROM task_assignments WHERE task_id = ? AND status = 'completed'",
            (task_id,),
        ).fetchone()["total"]
        if task_is_edit_locked(task["task_type"], int(approved or 0)):
            return api_error("该任务已有审核通过的提交，不能再编辑", 409)
        payload = request.get_json(silent=True) or {}
        title = str(payload.get("title", "")).strip()[:80]
        description = str(payload.get("description", "")).strip()[:240]
        category = str(payload.get("category", task["category"])).strip()[:30] or "生活"
        task_type = str(payload.get("task_type", task["task_type"])).lower()
        difficulty = str(payload.get("difficulty", task["difficulty"])).lower()
        icon = str(payload.get("icon") or task["icon"])
        due_date_value = str(payload.get("due_date") or "").strip()
        try:
            reward_coins = positive_int(payload.get("reward_coins", task["reward_coins"]), "积分奖励")
            reward_exp = positive_int(payload.get("reward_exp", task["reward_exp"]), "经验奖励")
            due_date = valid_date(due_date_value) if due_date_value else None
            # 未传的重复字段回退到原值，避免局部更新把规则清空
            repeat_rule = normalize_repeat_rule(
                {
                    "repeat_freq": payload.get("repeat_freq", task["repeat_freq"]),
                    "repeat_days": payload.get("repeat_days", task["repeat_days"]),
                    "repeat_month_week": payload.get("repeat_month_week", task["repeat_month_week"]),
                    "repeat_start": payload.get("repeat_start", task["repeat_start"]),
                    "repeat_end": payload.get("repeat_end", task["repeat_end"]),
                },
                task_type,
            )
        except ValueError as exc:
            return api_error(str(exc))
        if not title:
            return api_error("任务标题不能为空")
        if task_type not in TASK_TYPES or difficulty not in TASK_DIFFICULTIES:
            return api_error("任务类型或难度无效")
        if not valid_project_icon(icon):
            return api_error("任务图标无效")
        conn.execute(
            """
            UPDATE tasks SET title = ?, description = ?, category = ?, task_type = ?, difficulty = ?,
                reward_coins = ?, reward_exp = ?, icon = ?, due_date = ?,
                repeat_freq = ?, repeat_days = ?, repeat_month_week = ?, repeat_start = ?, repeat_end = ?
            WHERE id = ?
            """,
            (
                title,
                description,
                category,
                task_type,
                difficulty,
                reward_coins,
                reward_exp,
                icon,
                due_date,
                repeat_rule["repeat_freq"],
                repeat_rule["repeat_days"],
                repeat_rule["repeat_month_week"],
                repeat_rule["repeat_start"],
                repeat_rule["repeat_end"],
                task_id,
            ),
        )
        return jsonify(state_payload(conn, user))


@app.post("/api/tasks/<int:task_id>/claim")
@require_user
def claim_task(task_id: int):
    with connection() as conn:
        user = current_user(conn)
        if user["role"] != "child":
            return api_error("只有孩子账号可以领取任务", 403)
        task = conn.execute("SELECT * FROM tasks WHERE id = ? AND is_active = 1", (task_id,)).fetchone()
        if task is None:
            return api_error("任务不存在", 404)
        today = current_date()
        if task["due_date"] and task["due_date"] < today:
            return api_error("这个任务已经过期", 409)
        if task["task_type"] == "repeat" and not repeat_matches(task, date.fromisoformat(today)):
            return api_error("这个任务今天不触发，到那天会自动出现", 409)
        if task["task_type"] == "epic":
            existing = conn.execute(
                "SELECT 1 FROM task_assignments WHERE task_id = ? AND account_id = ? AND status IN ('claimed', 'submitted', 'completed')",
                (task_id, user["id"]),
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT status FROM task_assignments WHERE task_id = ? AND account_id = ? AND claim_date = ?",
                (task_id, user["id"], today),
            ).fetchone()
        if existing is not None:
            # 当天已有记录：若被退回，引导直接重新提交，避免撞 UNIQUE(task_id, account_id, claim_date)
            status = existing["status"] if "status" in existing.keys() else None
            if status == "rejected":
                return api_error("这个任务已被退回，请直接重新提交", 409)
            return api_error("你已经领取过这个任务", 409)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        cursor = conn.execute(
            """
            INSERT INTO task_assignments(task_id, account_id, status, claim_date, claimed_at)
            VALUES (?, ?, 'claimed', ?, ?)
            """,
            (task_id, user["id"], today, now),
        )
        return jsonify({"assignment_id": cursor.lastrowid, **state_payload(conn, user)}), 201


@app.post("/api/task-assignments/<int:assignment_id>/submit")
@require_user
def submit_task(assignment_id: int):
    with connection() as conn:
        user = current_user(conn)
        assignment = conn.execute(
            "SELECT * FROM task_assignments WHERE id = ? AND account_id = ?",
            (assignment_id, user["id"]),
        ).fetchone()
        if user["role"] != "child" or assignment is None:
            return api_error("任务领取记录不存在", 404)
        if assignment["status"] not in ("claimed", "rejected"):
            return api_error("当前任务状态不能提交", 409)
        # v0.11.0 每日提交审核额度：按「当天提交总次数」计数，被退回后重新提交也算一次。
        today = current_date()
        limit = daily_submit_limit_for(conn, int(user["id"]))
        if limit:
            used = submit_count_today(conn, int(user["id"]), today)
            if used >= limit:
                return api_error(
                    f"今天的提交审核次数已用完（每天 {limit} 次），明天再来吧；也可以请家长调整这个额度。",
                    429,
                )
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE task_assignments SET status = 'submitted', submitted_at = ?, review_note = NULL WHERE id = ?",
            (now, assignment_id),
        )
        conn.execute(
            """
            INSERT INTO task_submit_log(account_id, task_id, assignment_id, submit_date, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], assignment["task_id"], assignment_id, today, now),
        )
        return jsonify(state_payload(conn, user))


@app.post("/api/task-assignments/<int:assignment_id>/approve")
@require_admin
def approve_task(assignment_id: int):
    with connection() as conn:
        user = current_user(conn)
        assignment = conn.execute(
            """
            SELECT ta.*, t.title, t.reward_coins, t.reward_exp, t.task_type,
                   a.display_name AS account_name
            FROM task_assignments ta
            JOIN tasks t ON t.id = ta.task_id
            JOIN accounts a ON a.id = ta.account_id
            WHERE ta.id = ?
            """,
            (assignment_id,),
        ).fetchone()
        if assignment is None or assignment["status"] != "submitted":
            return api_error("待审核的任务提交不存在", 404)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        reward_coins = adjusted_earn_coins(conn, int(assignment["account_id"]), int(assignment["reward_coins"]))
        conn.execute(
            "INSERT INTO records(account_id, title, amount, type, date, time, created_at) VALUES (?, ?, ?, 'income', ?, ?, ?)",
            (
                assignment["account_id"],
                f"任务完成：{assignment['title']}",
                reward_coins,
                current_date(),
                current_time(),
                now,
            ),
        )
        conn.execute(
            "UPDATE task_assignments SET status = 'completed', completed_at = ?, reviewer_id = ?, review_note = NULL WHERE id = ?",
            (now, user["id"], assignment_id),
        )
        unlock_achievements(conn, int(assignment["account_id"]))
        return jsonify(state_payload(conn, user))


@app.post("/api/task-assignments/<int:assignment_id>/reject")
@require_admin
def reject_task(assignment_id: int):
    payload = request.get_json(silent=True) or {}
    reason = str(payload.get("reason", "请完成任务后重新提交")).strip()[:200] or "请完成任务后重新提交"
    with connection() as conn:
        user = current_user(conn)
        assignment = conn.execute(
            "SELECT id FROM task_assignments WHERE id = ? AND status = 'submitted'",
            (assignment_id,),
        ).fetchone()
        if assignment is None:
            return api_error("待审核的任务提交不存在", 404)
        conn.execute(
            "UPDATE task_assignments SET status = 'rejected', reviewer_id = ?, review_note = ? WHERE id = ?",
            (user["id"], reason, assignment_id),
        )
        return jsonify(state_payload(conn, user))


@app.get("/api/announcements")
@require_user
def list_announcements():
    with connection() as conn:
        user = current_user(conn)
        return jsonify({"announcements": announcement_rows(conn, user)})


@app.post("/api/announcements")
@require_admin
def create_announcement():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()[:80]
    content = str(payload.get("content", "")).strip()[:500]
    audience = str(payload.get("audience", "all")).lower()
    if not title or not content:
        return api_error("公告标题和内容不能为空")
    if audience not in {"all", "children"}:
        return api_error("公告范围无效")
    with connection() as conn:
        user = current_user(conn)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        cursor = conn.execute(
            """
            INSERT INTO announcements(title, content, audience, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, content, audience, user["id"], now, now),
        )
        return jsonify({"announcement_id": cursor.lastrowid, **state_payload(conn, user)}), 201


@app.route("/api/announcements/<int:announcement_id>", methods=["PUT", "DELETE"])
@require_admin
def announcement_detail(announcement_id: int):
    with connection() as conn:
        user = current_user(conn)
        existing = conn.execute(
            "SELECT * FROM announcements WHERE id = ? AND is_active = 1",
            (announcement_id,),
        ).fetchone()
        if existing is None:
            return api_error("公告不存在", 404)
        if request.method == "DELETE":
            conn.execute("UPDATE announcements SET is_active = 0 WHERE id = ?", (announcement_id,))
            return jsonify({"deleted": True, **state_payload(conn, user)})
        payload = request.get_json(silent=True) or {}
        title = str(payload.get("title", "")).strip()[:80]
        content = str(payload.get("content", "")).strip()[:500]
        audience = str(payload.get("audience", existing["audience"])).lower()
        if not title or not content:
            return api_error("公告标题和内容不能为空")
        if audience not in {"all", "children"}:
            return api_error("公告范围无效")
        conn.execute(
            "UPDATE announcements SET title = ?, content = ?, audience = ?, updated_at = ? WHERE id = ?",
            (title, content, audience, datetime.now().astimezone().isoformat(timespec="seconds"), announcement_id),
        )
        return jsonify(state_payload(conn, user))


@app.post("/api/transactions")
@require_user
def create_transaction():
    payload = request.get_json(silent=True) or {}
    kind = str(payload.get("kind", "")).lower()
    try:
        with connection() as conn:
            user = current_user(conn)
            if user["role"] == "child" and kind == "deduct":
                return api_error("孩子账号不能直接扣取积分，请使用兑换奖励", 403)
            if kind == "cash_exchange" and user["role"] != "child":
                return api_error("只有孩子账号可以兑换现金", 403)
            account_id = active_child_id(conn, user)
            if account_id is None:
                return api_error("当前没有可用的孩子账号")
            name = str(payload.get("name", "")).strip()
            points_value = payload.get("points")
            transaction_type = "income"
            if kind == "earn":
                item_id = int(payload.get("item_id")) if payload.get("item_id") is not None else None
                if item_id:
                    item = conn.execute("SELECT name, points FROM earn_items WHERE id = ? AND account_id = ?", (item_id, account_id)).fetchone()
                    if item is None:
                        return api_error("赚取项目不存在", 404)
                    name, points_value = item["name"], item["points"]
                points = positive_int(points_value)
                amount = adjusted_earn_coins(conn, account_id, points) if user["role"] == "child" else points
            elif kind == "deduct":
                item_id = int(payload.get("item_id")) if payload.get("item_id") is not None else None
                if item_id:
                    item = conn.execute("SELECT name, points FROM deduct_items WHERE id = ? AND account_id = ?", (item_id, account_id)).fetchone()
                    if item is None:
                        return api_error("扣取项目不存在", 404)
                    name, points_value = item["name"], item["points"]
                points = positive_int(points_value)
                amount = -points
                transaction_type = "expense"
            elif kind == "exchange":
                reward_id = int(payload.get("reward_id")) if payload.get("reward_id") is not None else None
                if reward_id:
                    reward = conn.execute("SELECT name, points FROM rewards WHERE id = ? AND account_id = ?", (reward_id, account_id)).fetchone()
                    if reward is None:
                        return api_error("兑换奖励不存在", 404)
                    name, points_value = reward["name"], reward["points"]
                points = positive_int(points_value)
                charged_points = adjusted_exchange_coins(conn, account_id, points) if user["role"] == "child" else points
                if get_balance(conn, account_id) < charged_points:
                    return api_error("积分不足", 409)
                amount = -charged_points
                transaction_type = "expense"
            elif kind == "cash_exchange":
                points = positive_int(points_value, "兑换积分")
                charged_points = adjusted_exchange_coins(conn, account_id, points) if user["role"] == "child" else points
                if get_balance(conn, account_id) < charged_points:
                    return api_error("积分不足", 409)
                amount = -charged_points
                name = f"兑换现金 ¥{points / points_per_yuan(conn):.2f}"
                transaction_type = "expense"
            elif kind == "manual":
                try:
                    amount = int(points_value)
                except (TypeError, ValueError) as exc:
                    raise ValueError("积分数值必须是整数") from exc
                if amount == 0:
                    raise ValueError("积分数值不能为 0")
                name = f"补积分：{name}" if name else "补积分"
                transaction_type = "income" if amount > 0 else "expense"
            else:
                return api_error("不支持的交易类型")
            transaction_date = valid_date(payload.get("date"))
            transaction_time = str(payload.get("time") or current_time())[:5]
            if not name:
                name = transaction_date
            if user["role"] == "child" and amount < 0 and kind not in ("exchange", "cash_exchange"):
                return api_error("孩子账号不能扣除积分", 403)
            if user["role"] == "child" and kind in ("earn", "exchange", "manual", "cash_exchange"):
                cursor = conn.execute(
                    """
                    INSERT INTO point_requests(
                        account_id, requester_id, kind, title, amount, type, date, time, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        account_id,
                        user["id"],
                        kind,
                        name,
                        amount,
                        transaction_type,
                        transaction_date,
                        transaction_time,
                        datetime.now().astimezone().isoformat(timespec="seconds"),
                    ),
                )
                return jsonify({"request_submitted": True, "request_id": cursor.lastrowid, **state_payload(conn, user)}), 202
            cursor = conn.execute(
                "INSERT INTO records(account_id, title, amount, type, date, time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (account_id, name, amount, transaction_type, transaction_date, transaction_time, datetime.now().astimezone().isoformat(timespec="seconds")),
            )
            return jsonify({"record_id": cursor.lastrowid, **state_payload(conn, user)}), 201
    except (TypeError, ValueError) as exc:
        return api_error(str(exc))


@app.post("/api/requests/<int:request_id>/approve")
@require_admin
def approve_request(request_id: int):
    with connection() as conn:
        user = current_user(conn)
        point_request = conn.execute(
            "SELECT * FROM point_requests WHERE id = ? AND status = 'pending'", (request_id,)
        ).fetchone()
        if point_request is None:
            return api_error("待审核申请不存在或已经处理", 404)
        if point_request["amount"] < 0 and get_balance(conn, point_request["account_id"]) < abs(point_request["amount"]):
            return api_error("当前积分不足，无法通过兑换申请", 409)
        conn.execute(
            """
            INSERT INTO records(account_id, title, amount, type, date, time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                point_request["account_id"],
                point_request["title"],
                point_request["amount"],
                point_request["type"],
                point_request["date"],
                point_request["time"],
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
        )
        conn.execute(
            "UPDATE point_requests SET status = 'approved', reviewed_at = ?, reviewer_id = ? WHERE id = ?",
            (datetime.now().astimezone().isoformat(timespec="seconds"), user["id"], request_id),
        )
        return jsonify(state_payload(conn, user))


@app.post("/api/requests/<int:request_id>/reject")
@require_admin
def reject_request(request_id: int):
    payload = request.get_json(silent=True) or {}
    reason = str(payload.get("reason", "管理员拒绝了这条申请")).strip()[:200]
    with connection() as conn:
        user = current_user(conn)
        point_request = conn.execute(
            "SELECT id FROM point_requests WHERE id = ? AND status = 'pending'", (request_id,)
        ).fetchone()
        if point_request is None:
            return api_error("待审核申请不存在或已经处理", 404)
        conn.execute(
            "UPDATE point_requests SET status = 'rejected', reviewed_at = ?, reviewer_id = ?, reject_reason = ? WHERE id = ?",
            (datetime.now().astimezone().isoformat(timespec="seconds"), user["id"], reason or "管理员拒绝了这条申请", request_id),
        )
        return jsonify(state_payload(conn, user))


@app.post("/api/transactions/<int:record_id>/undo")
@require_user
def undo_transaction(record_id: int):
    with connection() as conn:
        user = current_user(conn)
        if user["role"] == "child":
            return api_error("孩子账号不能撤销积分记录", 403)
        account_id = active_child_id(conn, user)
        cursor = conn.execute("DELETE FROM records WHERE id = ? AND account_id = ?", (record_id, account_id))
        if cursor.rowcount == 0:
            return api_error("积分记录不存在", 404)
        return jsonify(state_payload(conn, user))


@app.post("/api/items/<kind>")
@require_admin
def create_item(kind: str):
    if kind not in ITEM_TABLES:
        return api_error("不支持的项目类型", 404)
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    icon = str(payload.get("icon") or ITEM_DEFAULT_ICONS[kind])
    try:
        points = positive_int(payload.get("points"))
    except ValueError as exc:
        return api_error(str(exc))
    if not name:
        return api_error("项目名称不能为空")
    if not valid_project_icon(icon):
        return api_error("项目图片类型无效")
    with connection() as conn:
        user = current_user(conn)
        account_id = active_child_id(conn, user)
        if account_id is None:
            return api_error("当前没有可用的孩子账号")
        table = ITEM_TABLES[kind]
        cursor = conn.execute(f"INSERT INTO {table}(account_id, name, points, icon) VALUES (?, ?, ?, ?)", (account_id, name, points, icon))
        row = conn.execute(f"SELECT id, name, points, icon FROM {table} WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify(row_item(row, kind)), 201


@app.route("/api/items/<kind>/<int:item_id>", methods=["PUT", "DELETE"])
@require_admin
def item_detail(kind: str, item_id: int):
    if kind not in ITEM_TABLES:
        return api_error("不支持的项目类型", 404)
    with connection() as conn:
        user = current_user(conn)
        account_id = active_child_id(conn, user)
        table = ITEM_TABLES[kind]
        existing = conn.execute(f"SELECT id, name, points, icon FROM {table} WHERE id = ? AND account_id = ?", (item_id, account_id)).fetchone()
        if existing is None:
            return api_error("项目不存在", 404)
        if request.method == "DELETE":
            conn.execute(f"DELETE FROM {table} WHERE id = ? AND account_id = ?", (item_id, account_id))
            return jsonify({"deleted": True})
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        icon = str(payload.get("icon") or existing["icon"] or ITEM_DEFAULT_ICONS[kind])
        if not name:
            return api_error("项目名称不能为空")
        if not valid_project_icon(icon):
            return api_error("项目图片类型无效")
        try:
            points = positive_int(payload.get("points"))
        except ValueError as exc:
            return api_error(str(exc))
        conn.execute(f"UPDATE {table} SET name = ?, points = ?, icon = ? WHERE id = ? AND account_id = ?", (name, points, icon, item_id, account_id))
        row = conn.execute(f"SELECT id, name, points, icon FROM {table} WHERE id = ?", (item_id,)).fetchone()
        return jsonify(row_item(row, kind))


@app.post("/api/system/clear")
@require_admin
def clear_points():
    with connection() as conn:
        user = current_user(conn)
        account_id = active_child_id(conn, user)
        conn.execute("DELETE FROM records WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM point_requests WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM task_assignments WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM account_achievements WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM app_settings WHERE key = ?", (adventure_level_key(account_id),))
        return jsonify(state_payload(conn, user))


@app.post("/api/system/reset")
@require_admin
def reset_system():
    with connection() as conn:
        user = current_user(conn)
        account_id = active_child_id(conn, user)
        if account_id is None:
            return api_error("当前没有可用的孩子账号")
        conn.execute("DELETE FROM records WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM point_requests WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM task_assignments WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM account_achievements WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM app_settings WHERE key = ?", (adventure_level_key(account_id),))
        for table in ("earn_items", "deduct_items", "rewards"):
            conn.execute(f"DELETE FROM {table} WHERE account_id = ?", (account_id,))
        seed_items_for_child(conn, account_id)
        return jsonify(state_payload(conn, user))


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return api_error("接口不存在", 404)
    return error


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "9696")), debug=False)


