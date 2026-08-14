# RewardHub

RewardHub（中文名“带娃神器”）是一套面向家庭的本地积分管理工具。管理员可以创建管理账号和孩子账号，设置加分、扣分和兑换奖励；孩子可以自行注册账号、申请加分、兑换奖励或兑换现金，孩子提交的申请由管理员审核后生效。

系统提供家庭监控总控、账户积分表、折合金额、审核中心、积分记录和账号变更日志，并支持男孩、女孩头像和本地图标。账号、积分和操作记录保存在本地数据目录中。

当前版本：`0.7.0`

## 本次更新

- 版本升级到 `0.7.0`。
- 增加积分兑换现金，默认 `100 积分 = 1 元`，管理员可以自定义比例。
- 孩子账号可以在登录页自行注册。
- 注册账号固定为孩子账号，支持男孩、女孩头像。
- 注册后自动生成默认加分、扣分和兑换项目。
- 管理员可以继续创建、修改和删除孩子账号。
- 增加孩子自助注册日志。
- 内置生活项目图标同步到加分、扣分和兑换项目。
- 增加日常任务、史诗悬赏、任务领取和完成审核。
- 增加经验值、冒险等级、等级特权和成就勋章。
- 增加总览通知、孩子端通知弹窗和管理员公告编辑。
- 等级特权同时作用于积分赚取、奖励兑换和现金兑换。

## 孩子账号自助注册

在登录页点击“注册孩子账号”，填写登录账号、孩子名称、密码并选择头像，提交后即可进入孩子账号。孩子注册不会创建管理员账号；孩子提交的加分、奖励兑换和现金兑换申请，仍需管理员审核。

## Docker Compose 部署

准备一个目录，并在其中创建 `docker-compose.yml`：

```yaml
services:
  rewardhub:
    image: ghcr.io/fcyl-12/rewardhub:latest
    container_name: rewardhub
    ports:
      - "9696:9696"
    environment:
      ADMIN_USERNAME: "${ADMIN_USERNAME:-}"
      ADMIN_PASSWORD: "${ADMIN_PASSWORD:-}"
    volumes:
      - ./points_data:/data
    restart: unless-stopped
```

启动：

```bash
docker compose pull
docker compose up -d
```

打开：`http://设备IP:9696`

更新：

```bash
docker compose pull
docker compose up -d
```

停止：

```bash
docker compose down
```

`points_data` 是数据目录。更新或重建容器时不要删除它，否则账号和积分数据会被清空。

## 首次创建管理员

首次启动且数据目录中没有管理员账号时，打开页面即可按引导创建管理员用户名和密码。

也可以在 `docker-compose.yml` 所在目录创建 `.env`，让容器首次启动时自动创建管理员：

```dotenv
ADMIN_USERNAME=your-admin
ADMIN_PASSWORD=change-this-password
```

管理员账号创建后，后续启动不会自动覆盖账号或密码。若数据目录中已经存在账号，安装向导不会重新创建管理员；需要保留数据时请使用已有账号，重新开始前请先备份数据。
