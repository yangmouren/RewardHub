import base64
import os
import tempfile
import unittest
from pathlib import Path


class PointsManagerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = cls.temp_dir.name
        os.environ["DATABASE_PATH"] = str(Path(cls.temp_dir.name) / "test.db")
        os.environ["ADMIN_USERNAME"] = "admin"
        os.environ["ADMIN_PASSWORD"] = "admin123"
        from app import (
            admin_credentials_from_env,
            admin_credentials_marker_path,
            app,
            connection,
            create_admin_account,
            init_db,
            mark_install_credentials_applied,
            migrate_legacy_admin_account,
            password_hash,
        )

        cls.app = app
        cls.client = app.test_client()
        cls.connection = connection
        cls.create_admin_account = create_admin_account
        cls.init_db = init_db
        cls.admin_credentials_marker_path = admin_credentials_marker_path
        cls.mark_install_credentials_applied = mark_install_credentials_applied
        cls.migrate_legacy_admin_account = migrate_legacy_admin_account
        cls.password_hash = password_hash
        cls.admin_credentials_from_env = admin_credentials_from_env

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        accounts = self.client.get("/api/accounts").get_json()["accounts"]
        for account in accounts:
            if account["role"] == "child" or account["username"] != "admin":
                self.client.delete(f"/api/accounts/{account['id']}")
        with type(self).connection() as conn:
            conn.execute("UPDATE app_settings SET value = '100' WHERE key = 'points_per_yuan'")
            conn.execute("DELETE FROM announcements")

    def create_child(self, username="child1", display_name="小明", password="child123"):
        response = self.client.post(
            "/api/accounts",
            json={"username": username, "display_name": display_name, "password": password, "role": "child"},
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def state(self):
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_starts_with_admin_only(self):
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        accounts = response.get_json()["accounts"]
        self.assertEqual({account["username"] for account in accounts}, {"admin"})

        data = self.state()
        self.assertIsNone(data["active_child"])
        self.assertEqual(data["total_points"], 0)
        self.assertEqual(data["earn_items"], [])
        self.assertEqual(data["deduct_items"], [])
        self.assertEqual(data["rewards"], [])
        self.assertEqual(len(data["account_overview"]), 1)

    def test_login_roles_and_child_isolation(self):
        self.create_child(username="child", display_name="小朋友")
        earn_id = self.state()["earn_items"][0]["id"]
        response = self.client.post("/api/transactions", json={"kind": "earn", "item_id": earn_id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["total_points"], 10)

        response = self.client.post(
            "/api/accounts",
            json={"username": "kid2", "display_name": "小明", "password": "kid12345", "role": "child"},
        )
        self.assertEqual(response.status_code, 201)
        kid2_id = response.get_json()["id"]
        response = self.client.post(
            "/api/accounts",
            json={"username": "manager2", "display_name": "家长二", "password": "manager123", "role": "admin"},
        )
        self.assertEqual(response.status_code, 201)
        actions = {log["action"] for log in self.state()["account_logs"]}
        self.assertIn("create_child", actions)
        self.assertIn("create_admin", actions)

        response = self.client.post("/api/auth/select-child", json={"child_id": kid2_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_points"], 0)

        response = self.client.post("/api/transactions", json={"kind": "earn", "points": 6, "name": "测试"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["total_points"], 6)

        self.client.post("/api/auth/logout")
        response = self.client.post("/api/auth/login", json={"username": "child", "password": "child123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_points"], 10)
        self.assertEqual(self.client.post("/api/system/reset").status_code, 403)

    def test_first_run_admin_setup(self):
        with type(self).connection() as conn:
            for table in ("account_logs", "point_requests", "records", "task_assignments", "account_achievements", "tasks", "earn_items", "deduct_items", "rewards", "accounts"):
                conn.execute(f"DELETE FROM {table}")

        try:
            self.client.post("/api/auth/logout")
            self.assertEqual(self.client.get("/api/setup/status").get_json(), {"configured": False})
            self.assertEqual(self.client.get("/api/state").status_code, 401)

            response = self.client.post(
                "/api/setup/admin",
                json={"username": "my-admin", "password": "secure123", "password_confirm": "secure123"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["user"]["username"], "my-admin")
            self.assertEqual(self.client.get("/api/setup/status").get_json(), {"configured": True})
            self.assertEqual(
                self.client.post(
                    "/api/setup/admin",
                    json={"username": "another-admin", "password": "secure123", "password_confirm": "secure123"},
                ).status_code,
                409,
            )
            self.client.post("/api/auth/logout")
            self.assertEqual(
                self.client.post("/api/auth/login", json={"username": "my-admin", "password": "secure123"}).status_code,
                200,
            )
        finally:
            with type(self).connection() as conn:
                for table in ("account_logs", "point_requests", "records", "earn_items", "deduct_items", "rewards", "accounts"):
                    conn.execute(f"DELETE FROM {table}")
                type(self).create_admin_account(conn, "admin", "admin123")

    def test_child_can_register_from_auth_flow(self):
        self.client.post("/api/auth/logout")
        response = self.client.post(
            "/api/auth/register-child",
            json={
                "username": "self-child",
                "display_name": "自助孩子",
                "password": "child123",
                "password_confirm": "child123",
                "avatar": "girl",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["user"]["role"], "child")
        self.assertEqual(data["user"]["avatar"], "girl")
        self.assertEqual(data["active_child"]["username"], "self-child")
        self.assertTrue(data["earn_items"])

        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post(
                "/api/auth/login", json={"username": "self-child", "password": "child123"}
            ).status_code,
            200,
        )
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertIn("register_child", {log["action"] for log in self.state()["account_logs"]})

    def test_child_registration_requires_admin_setup(self):
        with type(self).connection() as conn:
            conn.execute("DELETE FROM accounts")
        try:
            response = self.client.post(
                "/api/auth/register-child",
                json={
                    "username": "orphan-child",
                    "display_name": "孤立孩子",
                    "password": "child123",
                    "password_confirm": "child123",
                    "avatar": "boy",
                },
            )
            self.assertEqual(response.status_code, 409)
        finally:
            with type(self).connection() as conn:
                type(self).create_admin_account(conn, "admin", "admin123")

    def test_install_credentials_replace_only_untouched_legacy_admin(self):
        os.environ["ADMIN_USERNAME"] = "new-admin"
        os.environ["ADMIN_PASSWORD"] = "new-secret"
        try:
            with type(self).connection() as conn:
                type(self).migrate_legacy_admin_account(conn)
            self.client.post("/api/auth/logout")
            self.assertEqual(
                self.client.post("/api/auth/login", json={"username": "new-admin", "password": "new-secret"}).status_code,
                200,
            )
            self.client.post("/api/auth/logout")
            self.assertEqual(
                self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code,
                401,
            )
        finally:
            os.environ["ADMIN_USERNAME"] = "admin"
            os.environ["ADMIN_PASSWORD"] = "admin123"
            with type(self).connection() as conn:
                conn.execute(
                    "UPDATE accounts SET username = ?, password_hash = ?, display_name = ? WHERE role = 'admin'",
                    ("admin", type(self).password_hash("admin123"), "管理员"),
                )

    def test_install_credentials_replace_existing_custom_admin_once(self):
        os.environ["ADMIN_USERNAME"] = "wizard-admin"
        os.environ["ADMIN_PASSWORD"] = "wizard-secret"
        marker = type(self).admin_credentials_marker_path()
        marker.unlink(missing_ok=True)
        try:
            with type(self).connection() as conn:
                conn.execute(
                    "UPDATE accounts SET username = ?, password_hash = ? WHERE role = 'admin'",
                    ("old-admin", type(self).password_hash("old-secret")),
                )
            type(self).init_db()
            self.client.post("/api/auth/logout")
            self.assertEqual(
                self.client.post(
                    "/api/auth/login", json={"username": "wizard-admin", "password": "wizard-secret"}
                ).status_code,
                200,
            )
            self.assertEqual(
                self.client.post(
                    "/api/auth/login", json={"username": "old-admin", "password": "old-secret"}
                ).status_code,
                401,
            )

            with type(self).connection() as conn:
                conn.execute(
                    "UPDATE accounts SET password_hash = ? WHERE username = ?",
                    (type(self).password_hash("manual-secret"), "wizard-admin"),
                )
            type(self).init_db()
            self.assertEqual(
                self.client.post(
                    "/api/auth/login", json={"username": "wizard-admin", "password": "manual-secret"}
                ).status_code,
                200,
            )
        finally:
            os.environ["ADMIN_USERNAME"] = "admin"
            os.environ["ADMIN_PASSWORD"] = "admin123"
            with type(self).connection() as conn:
                conn.execute(
                    "UPDATE accounts SET username = ?, password_hash = ? WHERE role = 'admin'",
                    ("admin", type(self).password_hash("admin123")),
                )
            type(self).mark_install_credentials_applied(("admin", "admin123"))

    def test_install_credentials_support_base64_env_values(self):
        encoded_username = base64.b64encode("base64-admin".encode("utf-8")).decode("ascii")
        encoded_password = base64.b64encode("p@ss word#$".encode("utf-8")).decode("ascii")
        os.environ["ADMIN_USERNAME_B64"] = encoded_username
        os.environ["ADMIN_PASSWORD_B64"] = encoded_password
        try:
            self.assertEqual(
                type(self).admin_credentials_from_env(),
                ("base64-admin", "p@ss word#$"),
            )
        finally:
            os.environ.pop("ADMIN_USERNAME_B64", None)
            os.environ.pop("ADMIN_PASSWORD_B64", None)

    def test_child_transactions_require_admin_approval(self):
        self.create_child(username="child", display_name="小朋友")
        self.client.post("/api/auth/logout")
        response = self.client.post("/api/auth/login", json={"username": "child", "password": "child123"})
        earn_id = response.get_json()["earn_items"][0]["id"]

        response = self.client.post("/api/transactions", json={"kind": "earn", "item_id": earn_id})
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.get_json()["request_submitted"])
        self.assertEqual(response.get_json()["total_points"], 0)
        request_id = response.get_json()["request_id"]
        self.assertEqual(self.client.post(f"/api/requests/{request_id}/approve").status_code, 403)

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        requests = self.client.get("/api/state").get_json()["requests"]
        self.assertEqual(requests[0]["status"], "pending")
        response = self.client.post(f"/api/requests/{request_id}/approve")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["requests"][0]["status"], "approved")

        self.client.post("/api/auth/logout")
        response = self.client.post("/api/auth/login", json={"username": "child", "password": "child123"})
        self.assertEqual(response.get_json()["total_points"], 10)

    def test_v06_child_permissions_avatars_and_account_edit(self):
        self.create_child(username="child", display_name="小朋友")
        state = self.state()
        self.assertEqual(state["version"], "0.7.0")
        self.assertEqual(state["user"]["avatar"], "adult-male")
        self.assertEqual(state["active_child"]["avatar"], "boy")

        self.client.post("/api/auth/logout")
        child_login = self.client.post("/api/auth/login", json={"username": "child", "password": "child123"})
        self.assertEqual(child_login.status_code, 200)
        earn_id = child_login.get_json()["earn_items"][0]["id"]
        self.assertEqual(self.client.post("/api/transactions", json={"kind": "deduct", "item_id": earn_id}).status_code, 403)
        self.assertEqual(self.client.post("/api/transactions", json={"kind": "manual", "points": -1, "name": "负数"}).status_code, 403)

        response = self.client.post("/api/transactions", json={"kind": "earn", "item_id": earn_id})
        self.assertEqual(response.status_code, 202)
        earn_request_id = response.get_json()["request_id"]
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        response = self.client.post(f"/api/requests/{earn_request_id}/approve")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_points"], 10)
        response = self.client.post("/api/items/reward", json={"name": "测试兑换", "points": 5})
        self.assertEqual(response.status_code, 201)
        reward_id = response.get_json()["id"]

        self.client.post("/api/auth/logout")
        child_login = self.client.post("/api/auth/login", json={"username": "child", "password": "child123"})
        response = self.client.post("/api/transactions", json={"kind": "exchange", "reward_id": reward_id})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["total_points"], 10)
        exchange_request_id = response.get_json()["request_id"]
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        response = self.client.post(f"/api/requests/{exchange_request_id}/approve")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_points"], 5)

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        child_id = self.state()["active_child_id"]
        response = self.client.put(f"/api/accounts/{child_id}", json={"display_name": "新名字", "password": "newpass123", "avatar": "girl"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["display_name"], "新名字")
        self.assertEqual(response.get_json()["avatar"], "girl")
        self.assertIn("update_child", {log["action"] for log in self.state()["account_logs"]})

        self.client.post("/api/auth/logout")
        response = self.client.post("/api/auth/login", json={"username": "child", "password": "newpass123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["display_name"], "新名字")
        self.assertEqual(response.get_json()["user"]["avatar"], "girl")

    def test_currency_settings_and_cash_exchange_require_approval(self):
        self.create_child(username="cash-child", display_name="现金孩子")
        state = self.state()
        self.assertEqual(state["settings"]["points_per_yuan"], 100)

        response = self.client.put("/api/settings", json={"points_per_yuan": 250})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["settings"]["points_per_yuan"], 250)

        response = self.client.post("/api/transactions", json={"kind": "earn", "points": 500, "name": "管理员发放"})
        self.assertEqual(response.status_code, 201)
        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": "cash-child", "password": "child123"}).status_code,
            200,
        )
        response = self.client.post("/api/transactions", json={"kind": "cash_exchange", "points": 250})
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.get_json()["request_submitted"])
        self.assertEqual(response.get_json()["total_points"], 500)
        request_id = response.get_json()["request_id"]
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        response = self.client.post(f"/api/requests/{request_id}/approve")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_points"], 250)
        self.assertIn("兑换现金 ¥1.00", [record["title"] for record in response.get_json()["records"]])

    def test_adventure_level_can_be_managed_or_return_to_auto(self):
        self.create_child(username="level-child", display_name="等级孩子")
        response = self.client.put("/api/settings", json={"adventure_level": 7})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["settings"]["manual_adventure_level"], 7)
        self.assertEqual(data["settings"]["adventure_level_mode"], "manual")
        self.assertEqual(data["gamification"]["level"], 7)
        self.assertEqual(data["gamification"]["level_mode"], "manual")

        response = self.client.put("/api/settings", json={"adventure_level": "auto"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsNone(data["settings"]["manual_adventure_level"])
        self.assertEqual(data["settings"]["adventure_level_mode"], "auto")
        self.assertEqual(data["gamification"]["level"], 1)

    def test_level_benefits_raise_earnings_and_lower_exchange_cost(self):
        self.create_child(username="benefit-child", display_name="福利孩子")
        response = self.client.put("/api/settings", json={"adventure_level": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["gamification"]["earn_bonus_percent"], 10)
        self.assertEqual(response.get_json()["gamification"]["exchange_discount_percent"], 5)

        earn = self.client.post("/api/items/earn", json={"name": "等级加金币", "points": 10, "icon": "points.svg"})
        self.assertEqual(earn.status_code, 201)
        reward = self.client.post("/api/items/reward", json={"name": "等级兑换", "points": 50, "icon": "gift.svg"})
        self.assertEqual(reward.status_code, 201)
        self.assertEqual(
            self.client.post("/api/transactions", json={"kind": "earn", "points": 100, "name": "准备兑换余额"}).status_code,
            201,
        )

        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": "benefit-child", "password": "child123"}).status_code,
            200,
        )
        data = self.state()
        earn_item = next(item for item in data["earn_items"] if item["name"] == "等级加金币")
        reward_item = next(item for item in data["rewards"] if item["name"] == "等级兑换")
        self.assertEqual(earn_item["base_points"], 10)
        self.assertEqual(earn_item["points"], 11)
        self.assertEqual(reward_item["base_points"], 50)
        self.assertEqual(reward_item["points"], 47)

        response = self.client.post("/api/transactions", json={"kind": "earn", "item_id": earn_item["id"]})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(next(item for item in response.get_json()["requests"] if item["title"] == "等级加金币")["amount"], 11)
        response = self.client.post("/api/transactions", json={"kind": "cash_exchange", "points": 50})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(next(item for item in response.get_json()["requests"] if item["kind"] == "cash_exchange")["amount"], -47)

        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code, 200)
        response = self.client.post("/api/transactions", json={"kind": "earn", "points": 10, "name": "管理员发放"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["records"][0]["amount"], 10)

    def test_child_can_change_own_password(self):
        child = self.create_child(username="password-child", display_name="改密孩子")
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": child["username"], "password": "child123"})
        response = self.client.put(
            "/api/auth/password",
            json={"current_password": "wrong-password", "password": "newchild123", "password_confirm": "newchild123"},
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.put(
            "/api/auth/password",
            json={"current_password": "child123", "password": "newchild123", "password_confirm": "newchild123"},
        )
        self.assertEqual(response.status_code, 200)
        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": child["username"], "password": "child123"}).status_code,
            401,
        )
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": child["username"], "password": "newchild123"}).status_code,
            200,
        )
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertIn("change_password", {log["action"] for log in self.state()["account_logs"]})

    def test_password_updates_and_last_child_can_be_deleted(self):
        child = self.create_child(username="child", display_name="小朋友")
        manager = self.client.post(
            "/api/accounts",
            json={"username": "manager2", "display_name": "家长二", "password": "manager123", "role": "admin"},
        ).get_json()

        response = self.client.put(
            f"/api/accounts/{manager['id']}",
            json={"display_name": "新家长", "password": "manager456", "avatar": "adult-female"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["avatar"], "adult-female")
        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": "manager2", "password": "manager123"}).status_code,
            401,
        )
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": "manager2", "password": "manager456"}).status_code,
            200,
        )
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

        response = self.client.put(
            f"/api/accounts/{child['id']}",
            json={"display_name": "新名字", "password": "newpass123", "avatar": "girl"},
        )
        self.assertEqual(response.status_code, 200)
        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": "child", "password": "child123"}).status_code,
            401,
        )
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": "child", "password": "newpass123"}).status_code,
            200,
        )
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(self.client.delete(f"/api/accounts/{child['id']}").status_code, 200)
        self.assertIsNone(self.state()["active_child"])

    def test_earn_deduct_exchange_and_undo(self):
        self.create_child()
        state = self.state()
        earn_id = state["earn_items"][0]["id"]
        deduct_id = state["deduct_items"][1]["id"]
        self.assertEqual(self.client.post("/api/transactions", json={"kind": "earn", "item_id": earn_id}).status_code, 201)
        response = self.client.post("/api/transactions", json={"kind": "deduct", "item_id": deduct_id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["total_points"], 5)

        reward_id = self.state()["rewards"][0]["id"]
        self.assertEqual(self.client.post("/api/transactions", json={"kind": "exchange", "reward_id": reward_id}).status_code, 409)

        record_id = self.state()["records"][0]["id"]
        response = self.client.post(f"/api/transactions/{record_id}/undo")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total_points"], 10)

    def test_custom_items_and_manual_history(self):
        self.create_child()
        response = self.client.post("/api/items/earn", json={"name": "整理书桌", "points": 6, "icon": "computer.svg"})
        self.assertEqual(response.status_code, 201)
        item_id = response.get_json()["id"]
        self.assertEqual(response.get_json()["icon"], "computer.svg")

        response = self.client.put(f"/api/items/earn/{item_id}", json={"name": "整理书桌并复习", "points": 9, "icon": "game.svg"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "整理书桌并复习")
        self.assertEqual(response.get_json()["icon"], "game.svg")

        response = self.client.post("/api/items/earn", json={"name": "做饭", "points": 8, "icon": "cooking.svg"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["icon"], "cooking.svg")
        self.assertEqual(
            self.client.post("/api/items/earn", json={"name": "不使用的图标", "points": 8, "icon": "camera.svg"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/items/earn", json={"name": "水果", "points": 8, "icon": "apple.svg"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/items/earn",
                json={"name": "不允许的远程图标", "points": 8, "icon": "iconify:fluent-emoji:pot-of-food"},
            ).status_code,
            400,
        )

        response = self.client.post("/api/transactions", json={"kind": "manual", "name": "历史补录", "points": 12, "date": "2026-01-02"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["records"][0]["date"], "2026-01-02")

        self.assertEqual(self.client.delete(f"/api/items/earn/{item_id}").status_code, 200)

    def test_life_icons_are_shared_by_earn_deduct_and_reward(self):
        self.create_child()
        for kind, name in (("earn", "洗衣"), ("deduct", "洗碗"), ("reward", "购物")):
            response = self.client.post(
                f"/api/items/{kind}",
                json={"name": name, "points": 8, "icon": "laundry.svg"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["icon"], "laundry.svg")

    def test_rpg_task_lifecycle_rewards_coins_experience_and_achievement(self):
        child = self.create_child(username="questkid", display_name="任务玩家", password="quest123")
        response = self.client.post(
            "/api/tasks",
            json={
                "title": "清理 NAS 垃圾空间",
                "description": "清理完成后提交验收",
                "category": "NAS",
                "task_type": "epic",
                "difficulty": "hard",
                "reward_coins": 40,
                "reward_exp": 25,
                "icon": "computer.svg",
            },
        )
        self.assertEqual(response.status_code, 201)
        task_id = response.get_json()["task"]["id"]

        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "questkid", "password": "quest123"}).status_code, 200)
        response = self.client.post(f"/api/tasks/{task_id}/claim")
        self.assertEqual(response.status_code, 201)
        assignment_id = response.get_json()["assignment_id"]
        self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/submit").status_code, 200)

        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code, 200)
        response = self.client.post(f"/api/task-assignments/{assignment_id}/approve")
        self.assertEqual(response.status_code, 200)

        self.client.post("/api/auth/logout")
        response = self.client.post("/api/auth/login", json={"username": "questkid", "password": "quest123"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["gamification"]["coins"], 40)
        self.assertEqual(data["gamification"]["experience"], 25)
        self.assertTrue(any(item["achievement_key"] == "first-quest" and item["unlocked"] for item in data["achievements"]))

    def test_builtin_delivery_icon_is_allowed_and_unknown_icon_is_rejected(self):
        self.create_child(username="icon-child", display_name="Icon Child", password="child123")
        response = self.client.post(
            "/api/items/earn",
            json={"name": "快递取件", "points": 8, "icon": "emoji:delivery"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["icon"], "emoji:delivery")
        self.assertEqual(
            self.client.post(
                "/api/items/earn",
                json={"name": "未知图标", "points": 8, "icon": "emoji:not-a-real-icon"},
            ).status_code,
            400,
        )

    def test_announcements_can_be_published_edited_removed_and_seen_by_children(self):
        child = self.create_child(username="notice-child", display_name="Notice Child", password="child123")
        response = self.client.post(
            "/api/announcements",
            json={"title": "本周悬赏", "content": "完成家庭挑战领取金币", "audience": "children"},
        )
        self.assertEqual(response.status_code, 201)
        announcement_id = response.get_json()["announcement_id"]
        self.assertEqual(response.get_json()["announcements"][0]["title"], "本周悬赏")

        response = self.client.put(
            f"/api/announcements/{announcement_id}",
            json={"title": "更新后的悬赏", "content": "今晚前提交任务", "audience": "all"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["announcements"][0]["audience"], "all")

        self.client.post("/api/auth/logout")
        self.assertEqual(
            self.client.post("/api/auth/login", json={"username": child["username"], "password": "child123"}).status_code,
            200,
        )
        self.assertEqual(self.state()["announcements"][0]["title"], "更新后的悬赏")

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(self.client.delete(f"/api/announcements/{announcement_id}").status_code, 200)
        self.assertEqual(self.state()["announcements"], [])

    def test_clear_and_reset(self):
        self.create_child()
        self.client.post("/api/transactions", json={"kind": "earn", "points": 20, "name": "测试"})
        self.assertEqual(self.client.post("/api/system/clear").get_json()["total_points"], 0)
        self.client.post("/api/items/reward", json={"name": "临时奖励", "points": 1})
        data = self.client.post("/api/system/reset").get_json()
        self.assertEqual(data["total_points"], 0)
        self.assertEqual(len(data["rewards"]), 4)

    def test_custom_image_routes_find_uploaded_assets(self):
        for asset in ("child-boy", "child-girl", "adult-male", "adult-female", "account-log", "login-cover", "control-center"):
            response = self.client.get(f"/custom-assets/{asset}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content_type.startswith("image/"))
            response.close()


if __name__ == "__main__":
    unittest.main()
