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
        self.assertEqual(state["version"], "0.13.7")
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


    # ---- v0.13.7 重复任务 ----

    def test_repeat_task_rules_trigger_on_expected_days(self):
        from datetime import date

        from app import repeat_matches, repeat_rule_text

        self.create_child(username="repeat-child", display_name="习惯孩子")
        cases = [
            ("跳绳", {"repeat_freq": "daily"}, ["2026-09-12", "2026-09-14"], [], "每天"),
            ("练字10分钟", {"repeat_freq": "weekly", "repeat_days": [1, 2, 3, 4, 5]},
             ["2026-09-14", "2026-09-15", "2026-09-18"], ["2026-09-12", "2026-09-13"], "每周一、二、三、四、五"),
            ("打扫房间", {"repeat_freq": "weekly", "repeat_days": [6, 7]},
             ["2026-09-12", "2026-09-13", "2026-09-19"], ["2026-09-14"], "每周六、日"),
            ("打篮球", {"repeat_freq": "weekly", "repeat_days": [2, 4]},
             ["2026-09-15", "2026-09-17"], ["2026-09-12", "2026-09-14", "2026-09-16"], "每周二、四"),
            ("大扫除", {"repeat_freq": "monthly", "repeat_days": [6, 7], "repeat_month_week": 1},
             ["2026-09-05", "2026-09-06", "2026-10-03", "2026-10-04"], ["2026-09-12", "2026-09-27"],
             "每月第 1 个周六、日"),
            ("月末大扫除", {"repeat_freq": "monthly", "repeat_days": [6, 7], "repeat_month_week": 5},
             ["2026-09-26", "2026-09-27", "2026-10-31"], ["2026-09-05", "2026-09-06"],
             "每月最后一个周六、日"),
            ("每月第二个周三", {"repeat_freq": "monthly", "repeat_days": [3], "repeat_month_week": 2},
             ["2026-09-09", "2026-10-14"], ["2026-09-02", "2026-09-16"], "每月第 2 个周三"),
            ("21天习惯", {"repeat_freq": "daily", "repeat_start": "2026-09-12", "repeat_end": "2026-10-02"},
             ["2026-09-12", "2026-10-02"], ["2026-09-11", "2026-10-03"],
             "每天（09-12 起，10-02 止）"),
        ]
        for title, rule, hits, misses, expected_text in cases:
            created = self.client.post(
                "/api/tasks",
                json={
                    "title": title,
                    "task_type": "repeat",
                    "reward_coins": 10,
                    "reward_exp": 5,
                    "icon": "points.svg",
                    **rule,
                },
            )
            self.assertEqual(created.status_code, 201, title)
            task = next(item for item in created.get_json()["state"]["tasks"] if item["title"] == title)
            self.assertEqual(task["repeat_text"], expected_text, title)
            for value in hits:
                self.assertTrue(repeat_matches(task, date.fromisoformat(value)), f"{title} 应触发 {value}")
            for value in misses:
                self.assertFalse(repeat_matches(task, date.fromisoformat(value)), f"{title} 不应触发 {value}")
            self.assertEqual(self.client.delete(f"/api/tasks/{task['id']}").status_code, 200)

    def test_repeat_task_rules_are_validated(self):
        self.create_child(username="repeat-valid", display_name="校验孩子")
        base = {"task_type": "repeat", "reward_coins": 10, "reward_exp": 5, "icon": "points.svg"}
        # 每周/每月必须选星期
        self.assertEqual(
            self.client.post("/api/tasks", json={"title": "缺星期", "repeat_freq": "weekly", **base}).status_code,
            400,
        )
        # 「第几个」越界
        self.assertEqual(
            self.client.post(
                "/api/tasks",
                json={"title": "越界", "repeat_freq": "monthly", "repeat_days": [1], "repeat_month_week": 9, **base},
            ).status_code,
            400,
        )
        # 结束日期早于开始日期
        self.assertEqual(
            self.client.post(
                "/api/tasks",
                json={"title": "反了", "repeat_freq": "daily", "repeat_start": "2026-10-02", "repeat_end": "2026-09-12", **base},
            ).status_code,
            400,
        )
        # 未知频率
        self.assertEqual(
            self.client.post("/api/tasks", json={"title": "频率错", "repeat_freq": "hourly", **base}).status_code,
            400,
        )
        # 非重复任务不该写入重复字段
        created = self.client.post(
            "/api/tasks",
            json={
                "title": "普通日常",
                "task_type": "daily",
                "reward_coins": 10,
                "reward_exp": 5,
                "icon": "points.svg",
                "repeat_freq": "weekly",
                "repeat_days": [1],
            },
        )
        self.assertEqual(created.status_code, 201)
        task = next(item for item in created.get_json()["state"]["tasks"] if item["title"] == "普通日常")
        self.assertIsNone(task["repeat_freq"])
        self.assertEqual(task["repeat_text"], "")
        self.client.delete(f"/api/tasks/{task['id']}")

    def test_repeat_task_materializes_on_trigger_days_only(self):
        from datetime import date

        from app import ensure_repeat_assignments

        child = self.create_child(username="habit-child", display_name="习惯小孩", password="child123")
        base = {"task_type": "repeat", "reward_coins": 10, "reward_exp": 5, "icon": "points.svg"}
        daily_id = self.client.post(
            "/api/tasks", json={"title": "天天打卡", "repeat_freq": "daily", **base}
        ).get_json()["task"]["id"]
        monday_id = self.client.post(
            "/api/tasks", json={"title": "周一专属", "repeat_freq": "weekly", "repeat_days": [1], **base}
        ).get_json()["task"]["id"]

        monday = date(2026, 9, 14)
        tuesday = date(2026, 9, 15)
        with type(self).connection() as conn:
            first_run = ensure_repeat_assignments(conn, child["id"], monday)
            second_run = ensure_repeat_assignments(conn, child["id"], monday)
            monday_tasks = {
                row["task_id"]
                for row in conn.execute(
                    "SELECT task_id FROM task_assignments WHERE account_id = ? AND claim_date = ?",
                    (child["id"], monday.isoformat()),
                )
            }
            ensure_repeat_assignments(conn, child["id"], tuesday)
            tuesday_tasks = {
                row["task_id"]
                for row in conn.execute(
                    "SELECT task_id FROM task_assignments WHERE account_id = ? AND claim_date = ?",
                    (child["id"], tuesday.isoformat()),
                )
            }

        self.assertGreaterEqual(first_run, 2)
        self.assertEqual(second_run, 0, "重复物化必须幂等")
        self.assertIn(daily_id, monday_tasks)
        self.assertIn(monday_id, monday_tasks)
        self.assertIn(daily_id, tuesday_tasks)
        self.assertNotIn(monday_id, tuesday_tasks, "只在周一触发的任务不该在周二生成")
        self.client.delete(f"/api/tasks/{daily_id}")
        self.client.delete(f"/api/tasks/{monday_id}")

    def test_repeat_task_auto_appears_for_child_and_shows_upcoming_off_schedule(self):
        from datetime import date, datetime

        self.create_child(username="auto-child", display_name="自动孩子", password="child123")
        base = {"task_type": "repeat", "reward_coins": 10, "reward_exp": 5, "icon": "points.svg"}
        daily_id = self.client.post(
            "/api/tasks", json={"title": "每日跳绳", "repeat_freq": "daily", **base}
        ).get_json()["task"]["id"]
        # 选一个「不是今天」的星期，保证今天不触发
        other_weekday = datetime.now().astimezone().isoweekday() % 7 + 1
        rest_id = self.client.post(
            "/api/tasks",
            json={"title": "只在那天", "repeat_freq": "weekly", "repeat_days": [other_weekday], **base},
        ).get_json()["task"]["id"]

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "auto-child", "password": "child123"})
        child_state = self.state()
        today_task = next(item for item in child_state["tasks"] if item["title"] == "每日跳绳")
        self.assertTrue(today_task["active_today"])
        self.assertIsNotNone(today_task["my_assignment"], "当天该触发的重复任务应自动可见")
        self.assertEqual(today_task["my_assignment"]["status"], "claimed")
        # v0.13.7：当天不触发、但计划未结束的重复任务，孩子端以「未开始 · 下次 X」提前可见
        upcoming = next(item for item in child_state["tasks"] if item["title"] == "只在那天")
        self.assertFalse(upcoming["active_today"])
        self.assertIsNone(upcoming["my_assignment"], "未开始的任务不该被提前物化成已领取")
        self.assertIsNotNone(upcoming["next_date"], "未开始的任务要给出下一次触发日期")
        self.assertEqual(date.fromisoformat(upcoming["next_date"]).isoweekday(), other_weekday)
        # 当天能做的排在未开始的前面
        self.assertEqual(child_state["tasks"][0]["title"], "每日跳绳")

        # 孩子可以直接提交（仍走家长审核）
        submit = self.client.post(f"/api/task-assignments/{today_task['my_assignment']['id']}/submit")
        self.assertEqual(submit.status_code, 200)

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        admin_state = self.state()
        self.assertFalse(next(item for item in admin_state["tasks"] if item["title"] == "只在那天")["active_today"])
        self.assertIsNotNone(next(item for item in admin_state["tasks"] if item["title"] == "每日跳绳")["my_assignment"])
        self.client.delete(f"/api/tasks/{daily_id}")
        self.client.delete(f"/api/tasks/{rest_id}")


    def test_repeat_rule_survives_partial_update(self):
        self.create_child(username="repeat-edit", display_name="编辑孩子")
        created = self.client.post(
            "/api/tasks",
            json={
                "title": "打篮球",
                "task_type": "repeat",
                "reward_coins": 10,
                "reward_exp": 5,
                "icon": "points.svg",
                "repeat_freq": "weekly",
                "repeat_days": [2, 4],
            },
        )
        task_id = created.get_json()["task"]["id"]

        # 只改标题：重复规则必须保留
        response = self.client.put(f"/api/tasks/{task_id}", json={"title": "打篮球 1 小时"})
        self.assertEqual(response.status_code, 200)
        task = next(item for item in response.get_json()["tasks"] if item["id"] == task_id)
        self.assertEqual(task["title"], "打篮球 1 小时")
        self.assertEqual(task["repeat_days"], [2, 4])
        self.assertEqual(task["repeat_text"], "每周二、四")

        # 改成非重复类型：重复规则应清空
        response = self.client.put(
            f"/api/tasks/{task_id}", json={"title": "打篮球 1 小时", "task_type": "daily"}
        )
        self.assertEqual(response.status_code, 200)
        task = next(item for item in response.get_json()["tasks"] if item["id"] == task_id)
        self.assertIsNone(task["repeat_freq"])
        self.assertEqual(task["repeat_text"], "")
        self.client.delete(f"/api/tasks/{task_id}")


    # ---- v0.13.7 任务可见性 / 编辑删除 ----

    def test_next_repeat_occurrence_returns_exact_date(self):
        from datetime import date

        from app import next_repeat_occurrence

        monday_task = {
            "repeat_freq": "weekly",
            "repeat_days": "1",
            "repeat_month_week": None,
            "repeat_start": None,
            "repeat_end": None,
        }
        saturday = date(2026, 9, 12)  # 2026-09-12 是周六
        self.assertEqual(next_repeat_occurrence(monday_task, saturday), date(2026, 9, 14))
        # 当天就触发时返回当天
        self.assertEqual(next_repeat_occurrence(monday_task, date(2026, 9, 14)), date(2026, 9, 14))
        # 生效区间已过 → 没有下次
        self.assertIsNone(next_repeat_occurrence({**monday_task, "repeat_end": "2026-09-11"}, saturday))
        # 区间还没开始 → 落在区间内的第一个周一
        self.assertEqual(
            next_repeat_occurrence({**monday_task, "repeat_start": "2026-10-01"}, saturday), date(2026, 10, 5)
        )
        # 周二~周五：周六看到的下一次是下周二
        self.assertEqual(
            next_repeat_occurrence({**monday_task, "repeat_days": "2,3,4,5"}, saturday), date(2026, 9, 15)
        )

    def test_repeat_task_with_ended_window_is_hidden_from_child(self):
        from datetime import datetime, timedelta

        today = datetime.now().astimezone().date()
        self.create_child(username="ended-child", display_name="结束孩子", password="child123")
        ended_id = self.client.post(
            "/api/tasks",
            json={
                "title": "已经结束的习惯",
                "task_type": "repeat",
                "repeat_freq": "daily",
                "repeat_start": (today - timedelta(days=20)).isoformat(),
                "repeat_end": (today - timedelta(days=1)).isoformat(),
                "reward_coins": 10,
                "reward_exp": 5,
                "icon": "points.svg",
            },
        ).get_json()["task"]["id"]

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "ended-child", "password": "child123"})
        titles = [item["title"] for item in self.state()["tasks"]]
        self.assertNotIn("已经结束的习惯", titles, "生效区间已过的重复任务不该再出现")

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.client.delete(f"/api/tasks/{ended_id}")

    def test_child_cannot_claim_repeat_task_off_schedule(self):
        from datetime import datetime

        other_weekday = datetime.now().astimezone().isoweekday() % 7 + 1
        self.create_child(username="claim-child", display_name="领取孩子", password="child123")
        task_id = self.client.post(
            "/api/tasks",
            json={
                "title": "改日再练",
                "task_type": "repeat",
                "repeat_freq": "weekly",
                "repeat_days": [other_weekday],
                "reward_coins": 10,
                "reward_exp": 5,
                "icon": "points.svg",
            },
        ).get_json()["task"]["id"]

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "claim-child", "password": "child123"})
        response = self.client.post(f"/api/tasks/{task_id}/claim")
        self.assertEqual(response.status_code, 409)
        self.assertIn("今天不触发", response.get_json()["error"])

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.client.delete(f"/api/tasks/{task_id}")

    def test_admin_can_edit_and_delete_published_task(self):
        self.create_child(username="edit-child", display_name="编辑孩子", password="child123")
        task_id = self.client.post(
            "/api/tasks",
            json={"title": "倒垃圾", "task_type": "daily", "reward_coins": 10, "reward_exp": 5, "icon": "points.svg"},
        ).get_json()["task"]["id"]

        updated = self.client.put(
            f"/api/tasks/{task_id}",
            json={
                "title": "倒垃圾并套袋",
                "description": "记得套新袋子",
                "category": "生活",
                "task_type": "daily",
                "difficulty": "easy",
                "reward_coins": 15,
                "reward_exp": 8,
                "due_date": "",
                "icon": "chore.svg",
            },
        )
        self.assertEqual(updated.status_code, 200)
        task = next(item for item in updated.get_json()["tasks"] if item["id"] == task_id)
        self.assertEqual(task["title"], "倒垃圾并套袋")
        self.assertEqual(task["reward_coins"], 15)
        self.assertEqual(task["difficulty"], "easy")
        self.assertEqual(task["icon"], "chore.svg")

        # 孩子端看得到改动
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "edit-child", "password": "child123"})
        self.assertIn("倒垃圾并套袋", [item["title"] for item in self.state()["tasks"]])

        # 删除后双方都看不到（软删除 is_active=0）
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(self.client.delete(f"/api/tasks/{task_id}").status_code, 200)
        self.assertNotIn("倒垃圾并套袋", [item["title"] for item in self.state()["tasks"]])


    # ---- v0.13.7 审核中心：任务验收队列 ----

    def reset_task_state(self):
        """清掉历史用例遗留的任务/提交，保证审核队列断言不受执行顺序影响。"""
        with type(self).connection() as conn:
            conn.execute("DELETE FROM task_assignments")
            conn.execute("DELETE FROM task_submit_log")
            conn.execute("UPDATE tasks SET is_active = 0")

    def test_task_reviews_queue_exposes_submitted_tasks_to_admin(self):
        self.reset_task_state()
        self.create_child(username="review-child", display_name="验收孩子", password="child123")
        task_id = self.client.post(
            "/api/tasks",
            json={"title": "整理书桌", "task_type": "daily", "reward_coins": 12, "reward_exp": 6, "icon": "points.svg"},
        ).get_json()["task"]["id"]
        # 还没人提交 → 管理端审核队列为空
        self.assertEqual(self.state()["task_reviews"], [])

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "review-child", "password": "child123"})
        claim = self.client.post(f"/api/tasks/{task_id}/claim")
        self.assertEqual(claim.status_code, 201)
        assignment_id = claim.get_json()["assignment_id"]
        # 孩子端不该拿到管理端的审核队列
        self.assertEqual(self.state()["task_reviews"], [])
        self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/submit").status_code, 200)

        # 提交后管理端「审核中心」立刻能看到这条待验收
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        reviews = self.state()["task_reviews"]
        self.assertEqual(len(reviews), 1)
        review = reviews[0]
        self.assertEqual(review["assignment_id"], assignment_id)
        self.assertEqual(review["task_title"], "整理书桌")
        self.assertEqual(review["child_name"], "验收孩子")
        self.assertEqual(review["child_avatar"], "boy")
        self.assertEqual(review["reward_coins"], 12)
        self.assertTrue(review["task_active"])
        self.assertTrue(review["submitted_at"])
        # 总览的待办口径要算上任务验收
        child = next(item for item in self.state()["account_overview"] if item["username"] == "review-child")
        self.assertEqual(child["task_pending_count"], 1)
        self.assertEqual(child["pending_count"], 0)

        # 验收通过 → 出队并结算积分
        self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/approve").status_code, 200)
        self.assertEqual(self.state()["task_reviews"], [])

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "review-child", "password": "child123"})
        child_state = self.state()
        self.assertIn("任务完成：整理书桌", [record["title"] for record in child_state["records"]])
        self.assertGreaterEqual(child_state["total_points"], 12)

    def test_task_review_survives_task_withdrawn(self):
        self.reset_task_state()
        self.create_child(username="orphan-child", display_name="撤下孩子", password="child123")
        task_id = self.client.post(
            "/api/tasks",
            json={"title": "已被撤下的任务", "task_type": "daily", "reward_coins": 8, "reward_exp": 4, "icon": "points.svg"},
        ).get_json()["task"]["id"]
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "orphan-child", "password": "child123"})
        assignment_id = self.client.post(f"/api/tasks/{task_id}/claim").get_json()["assignment_id"]
        self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/submit").status_code, 200)

        # 任务被撤下（软删除）后孩子端看不到，但管理端仍必须能结算这次提交
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(self.client.delete(f"/api/tasks/{task_id}").status_code, 200)
        self.assertNotIn("已被撤下的任务", [item["title"] for item in self.state()["tasks"]])
        reviews = self.state()["task_reviews"]
        self.assertEqual([review["task_title"] for review in reviews], ["已被撤下的任务"])
        self.assertFalse(reviews[0]["task_active"])

        # 撤下的任务依然可以验收结算（否则会永远卡在「待验收」）
        self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/approve").status_code, 200)
        self.assertEqual(self.state()["task_reviews"], [])

    def test_task_edit_locks_after_approval(self):
        """v0.13.7：验收通过后不能再编辑（重复任务例外，它要长期复用）。"""
        self.reset_task_state()
        self.create_child(username="lock-child", display_name="锁定孩子", password="child123")
        base = {"reward_coins": 10, "reward_exp": 5, "icon": "points.svg"}
        daily_id = self.client.post(
            "/api/tasks", json={"title": "一次性任务", "task_type": "daily", **base}
        ).get_json()["task"]["id"]
        repeat_id = self.client.post(
            "/api/tasks", json={"title": "每日打卡", "task_type": "repeat", "repeat_freq": "daily", **base}
        ).get_json()["task"]["id"]

        def task_of(state, task_id):
            return next(item for item in state["tasks"] if item["id"] == task_id)

        admin_state = self.state()
        self.assertFalse(task_of(admin_state, daily_id)["edit_locked"])
        self.assertFalse(task_of(admin_state, repeat_id)["edit_locked"])

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "lock-child", "password": "child123"})
        daily_assignment = self.client.post(f"/api/tasks/{daily_id}/claim").get_json()["assignment_id"]
        self.assertEqual(self.client.post(f"/api/task-assignments/{daily_assignment}/submit").status_code, 200)
        # 重复任务当天会自动物化为「已领取」，孩子直接提交即可
        repeat_assignment = task_of(self.state(), repeat_id)["my_assignment"]["id"]
        self.assertEqual(self.client.post(f"/api/task-assignments/{repeat_assignment}/submit").status_code, 200)

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        for assignment_id in (daily_assignment, repeat_assignment):
            self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/approve").status_code, 200)

        state = self.state()
        self.assertEqual(task_of(state, daily_id)["approved_count"], 1)
        self.assertTrue(task_of(state, daily_id)["edit_locked"], "验收通过后一次性任务应锁定编辑")
        self.assertFalse(task_of(state, repeat_id)["edit_locked"], "重复任务要长期复用，不能锁定编辑")

        # 后端拦截：改标题/奖励一律 409，且原任务保持不变
        locked = self.client.put(f"/api/tasks/{daily_id}", json={"title": "偷偷改标题", "task_type": "daily", **base})
        self.assertEqual(locked.status_code, 409)
        self.assertEqual(task_of(self.state(), daily_id)["title"], "一次性任务")

        # 重复任务仍可正常编辑
        allowed = self.client.put(
            f"/api/tasks/{repeat_id}",
            json={"title": "每日打卡（改）", "task_type": "repeat", "repeat_freq": "daily", **base},
        )
        self.assertEqual(allowed.status_code, 200)

    def test_task_review_rejects_and_child_can_resubmit(self):
        self.reset_task_state()
        self.create_child(username="redo-child", display_name="重做孩子", password="child123")
        task_id = self.client.post(
            "/api/tasks",
            json={"title": "重做示例", "task_type": "daily", "reward_coins": 9, "reward_exp": 4, "icon": "points.svg"},
        ).get_json()["task"]["id"]
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "redo-child", "password": "child123"})
        assignment_id = self.client.post(f"/api/tasks/{task_id}/claim").get_json()["assignment_id"]
        self.client.post(f"/api/task-assignments/{assignment_id}/submit")

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        response = self.client.post(
            f"/api/task-assignments/{assignment_id}/reject", json={"reason": "请重新整理"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.state()["task_reviews"], [])

        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "redo-child", "password": "child123"})
        task = next(item for item in self.state()["tasks"] if item["title"] == "重做示例")
        self.assertEqual(task["my_assignment"]["status"], "rejected")
        self.assertEqual(task["my_assignment"]["review_note"], "请重新整理")
        # 被退回后可以直接重新提交，重新进入管理端审核队列
        self.assertEqual(self.client.post(f"/api/task-assignments/{assignment_id}/submit").status_code, 200)
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(len(self.state()["task_reviews"]), 1)


    # ---- v0.13.7 每日提交审核额度 ----
    def switch_user(self, username, password="child123"):
        self.client.post("/api/auth/logout")
        response = self.client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200)
        return response

    def login_admin(self):
        return self.switch_user("admin", "admin123")

    def publish_daily_task(self, title):
        response = self.client.post(
            "/api/tasks",
            json={"title": title, "task_type": "daily", "reward_coins": 5, "reward_exp": 2, "icon": "points.svg"},
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()["task"]

    def submit_task_named(self, title):
        task = next(item for item in self.state()["tasks"] if item["title"] == title)
        assignment = task["my_assignment"]
        if assignment is None:
            assignment_id = self.client.post(f"/api/tasks/{task['id']}/claim").get_json()["assignment_id"]
        else:
            assignment_id = assignment["id"]
        return self.client.post(f"/api/task-assignments/{assignment_id}/submit"), assignment_id

    def set_submit_limit(self, username, limit):
        self.login_admin()
        account = next(a for a in self.client.get("/api/accounts").get_json()["accounts"] if a["username"] == username)
        return self.client.put(
            f"/api/accounts/{account['id']}",
            json={"display_name": account["display_name"], "avatar": account["avatar"], "daily_submit_limit": limit},
        )

    def test_daily_submit_limit_defaults_to_ten(self):
        self.reset_task_state()
        self.create_child(username="quota-child", display_name="额度孩子", password="child123")
        self.switch_user("quota-child")
        quota = self.state()["submit_quota"]
        self.assertEqual(quota, {"limit": 10, "used": 0, "unlimited": False, "remaining": 10})

        self.login_admin()
        child = next(a for a in self.state()["account_overview"] if a["username"] == "quota-child")
        self.assertEqual(child["daily_submit_limit"], 10)
        self.assertEqual(child["today_submit_count"], 0)

    def test_create_account_accepts_submit_limit(self):
        response = self.client.post(
            "/api/accounts",
            json={
                "username": "quota-new",
                "display_name": "新额度孩子",
                "password": "child123",
                "role": "child",
                "daily_submit_limit": 3,
            },
        )
        self.assertEqual(response.status_code, 201)
        child = next(a for a in self.state()["account_overview"] if a["username"] == "quota-new")
        self.assertEqual(child["daily_submit_limit"], 3)

    def test_submit_limit_blocks_after_quota_used_up(self):
        self.reset_task_state()
        self.create_child(username="quota-block", display_name="限额孩子", password="child123")
        self.assertEqual(self.set_submit_limit("quota-block", 2).status_code, 200)
        self.publish_daily_task("任务A")
        self.publish_daily_task("任务B")
        self.publish_daily_task("任务C")

        self.switch_user("quota-block")
        for title in ("任务A", "任务B"):
            response, _ = self.submit_task_named(title)
            self.assertEqual(response.status_code, 200, title)
        quota = self.state()["submit_quota"]
        self.assertEqual(quota["used"], 2)
        self.assertEqual(quota["remaining"], 0)

        blocked, _ = self.submit_task_named("任务C")
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("已用完", blocked.get_json()["error"])
        # 被拦截的提交不能落库，也不能占额度
        self.assertEqual(self.state()["submit_quota"]["used"], 2)
        task_c = next(item for item in self.state()["tasks"] if item["title"] == "任务C")
        self.assertEqual(task_c["my_assignment"]["status"], "claimed")

        self.login_admin()
        child = next(a for a in self.state()["account_overview"] if a["username"] == "quota-block")
        self.assertEqual(child["today_submit_count"], 2)
        self.assertEqual(len(self.state()["task_reviews"]), 2)

    def test_resubmit_after_reject_consumes_quota(self):
        self.reset_task_state()
        self.create_child(username="quota-redo", display_name="重做孩子", password="child123")
        self.assertEqual(self.set_submit_limit("quota-redo", 2).status_code, 200)
        self.publish_daily_task("重做任务")
        self.publish_daily_task("后续任务")

        self.switch_user("quota-redo")
        first, assignment_id = self.submit_task_named("重做任务")
        self.assertEqual(first.status_code, 200)
        self.login_admin()
        self.assertEqual(
            self.client.post(f"/api/task-assignments/{assignment_id}/reject", json={"reason": "重做"}).status_code, 200
        )
        # 被退回后重新提交：第 2 次提交，额度用尽
        self.switch_user("quota-redo")
        again = self.client.post(f"/api/task-assignments/{assignment_id}/submit")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(self.state()["submit_quota"]["used"], 2)

        blocked, _ = self.submit_task_named("后续任务")
        self.assertEqual(blocked.status_code, 429)

    def test_zero_limit_means_unlimited(self):
        self.reset_task_state()
        self.create_child(username="quota-free", display_name="不限孩子", password="child123")
        self.assertEqual(self.set_submit_limit("quota-free", 1).status_code, 200)
        self.publish_daily_task("一次性任务")
        self.publish_daily_task("继续任务")

        self.switch_user("quota-free")
        self.assertEqual(self.submit_task_named("一次性任务")[0].status_code, 200)
        self.assertEqual(self.submit_task_named("继续任务")[0].status_code, 429)

        # 家长改成 0 → 不限制，之前被拦的提交立刻可以继续
        self.assertEqual(self.set_submit_limit("quota-free", 0).status_code, 200)
        self.switch_user("quota-free")
        quota = self.state()["submit_quota"]
        self.assertTrue(quota["unlimited"])
        self.assertIsNone(quota["remaining"])
        self.assertEqual(self.submit_task_named("继续任务")[0].status_code, 200)

    def test_submit_limit_is_per_child(self):
        self.reset_task_state()
        self.create_child(username="quota-a", display_name="孩子A", password="child123")
        self.create_child(username="quota-b", display_name="孩子B", password="child123")
        self.assertEqual(self.set_submit_limit("quota-a", 1).status_code, 200)
        self.assertEqual(self.set_submit_limit("quota-b", 5).status_code, 200)
        self.publish_daily_task("共享任务")

        self.switch_user("quota-a")
        self.assertEqual(self.submit_task_named("共享任务")[0].status_code, 200)
        self.assertEqual(self.state()["submit_quota"]["used"], 1)

        # 孩子B 的额度不受孩子A 影响
        self.switch_user("quota-b")
        self.assertEqual(self.state()["submit_quota"], {"limit": 5, "used": 0, "unlimited": False, "remaining": 5})
        self.assertEqual(self.submit_task_named("共享任务")[0].status_code, 200)
        self.assertEqual(self.state()["submit_quota"]["used"], 1)

        self.login_admin()
        overview = {item["username"]: item for item in self.state()["account_overview"]}
        self.assertEqual(overview["quota-a"]["today_submit_count"], 1)
        self.assertEqual(overview["quota-b"]["today_submit_count"], 1)
        self.assertEqual(overview["quota-a"]["daily_submit_limit"], 1)
        self.assertEqual(overview["quota-b"]["daily_submit_limit"], 5)

    def test_submit_limit_validation_and_persistence(self):
        self.create_child(username="quota-val", display_name="校验孩子", password="child123")
        for bad in (-1, 1000, "abc", 2.5):
            response = self.set_submit_limit("quota-val", bad)
            self.assertEqual(response.status_code, 400, f"应拒绝 {bad!r}")
        self.assertEqual(
            next(a for a in self.state()["account_overview"] if a["username"] == "quota-val")["daily_submit_limit"], 10
        )
        # 不带该字段的更新不应把额度清掉
        self.login_admin()
        account = next(a for a in self.client.get("/api/accounts").get_json()["accounts"] if a["username"] == "quota-val")
        self.client.put(
            f"/api/accounts/{account['id']}",
            json={"display_name": "改名孩子", "avatar": account["avatar"], "daily_submit_limit": 7},
        )
        self.client.put(
            f"/api/accounts/{account['id']}",
            json={"display_name": "再改名孩子", "avatar": account["avatar"]},
        )
        child = next(a for a in self.state()["account_overview"] if a["username"] == "quota-val")
        self.assertEqual(child["display_name"], "再改名孩子")
        self.assertEqual(child["daily_submit_limit"], 7)

    def test_submit_log_records_each_submission_event(self):
        self.reset_task_state()
        self.create_child(username="quota-log", display_name="日志孩子", password="child123")
        task = self.publish_daily_task("日志任务")
        self.switch_user("quota-log")
        _, assignment_id = self.submit_task_named("日志任务")
        with type(self).connection() as conn:
            rows = conn.execute(
                "SELECT account_id, task_id, assignment_id, submit_date FROM task_submit_log"
            ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["task_id"], task["id"])
        self.assertEqual(rows[0]["assignment_id"], assignment_id)
        self.assertEqual(rows[0]["submit_date"], __import__("app").current_date())

    def test_deleting_child_clears_its_submit_log(self):
        self.reset_task_state()
        account = self.create_child(username="quota-del", display_name="删除孩子", password="child123")
        self.publish_daily_task("删除任务")
        self.switch_user("quota-del")
        self.assertEqual(self.submit_task_named("删除任务")[0].status_code, 200)
        self.login_admin()
        self.assertEqual(self.client.delete(f"/api/accounts/{account['id']}").status_code, 200)
        with type(self).connection() as conn:
            remaining = conn.execute(
                "SELECT COUNT(*) FROM task_submit_log WHERE account_id = ?", (account["id"],)
            ).fetchone()[0]
        self.assertEqual(remaining, 0)


    def test_export_contains_every_table(self):
        self.create_child()
        payload = self.client.get("/api/export").get_json()
        self.assertEqual(payload["version"], "0.13.7")
        for table in (
            "accounts", "earn_items", "deduct_items", "rewards", "records",
            "point_requests", "account_logs", "app_settings", "tasks",
            "task_assignments", "task_submit_log", "achievements",
            "account_achievements", "announcements",
        ):
            self.assertIn(table, payload["data"])

    def test_import_overwrites_data_and_backs_up_first(self):
        child = self.create_child(username="import-kid", display_name="导入孩子")
        snapshot = self.client.get("/api/export").get_json()
        try:
            self.assertEqual(self.client.delete(f"/api/accounts/{child['id']}").status_code, 200)
            usernames = {a["username"] for a in self.client.get("/api/accounts").get_json()["accounts"]}
            self.assertNotIn("import-kid", usernames)

            response = self.client.post("/api/import", json=snapshot)
            self.assertEqual(response.status_code, 200)
            body = response.get_json()
            self.assertTrue(body["imported"])
            self.assertFalse(body["relogin"])
            self.assertTrue(body["backup"])
            self.assertIsNotNone(body["state"])
            usernames = {a["username"] for a in self.client.get("/api/accounts").get_json()["accounts"]}
            self.assertIn("import-kid", usernames)
            self.assertIn("accounts", body["tables"])
        finally:
            # 覆盖式导入会动整库，用完立刻还原快照，避免污染后面的用例
            self.client.post("/api/import", json=snapshot)

    def test_import_rejects_invalid_payload(self):
        cases = [
            {},
            {"data": []},
            {"data": {}},
            {"data": {"evil_table": []}},
            {"data": {"accounts": "not-a-list"}},
            {"data": {"accounts": [1, 2]}},
        ]
        for payload in cases:
            response = self.client.post("/api/import", json=payload)
            self.assertEqual(response.status_code, 400, f"应拒绝 {payload!r}")


if __name__ == "__main__":
    unittest.main()
