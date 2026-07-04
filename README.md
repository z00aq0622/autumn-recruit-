# 秋招自动推送系统 (AutumnRecruit-AutoPush)

> 🐗 每日自动爬取浙大就业中心 + Boss直聘 + 国聘网 + 牛客网 + 目标城市就业网，智能匹配评分，微信推送日报

## ✨ 功能

- 🔍 **5大数据源**: 浙大就业中心、Boss直聘校招、国聘网、牛客网、目标城市就业网
- 🎯 **智能匹配**: 7维度评分系统，自动筛选最匹配你的岗位
- 📱 **微信推送**: 每日9:00自动推送到微信（Server酱）
- ⏰ **全自动运行**: GitHub Actions 定时任务，无需本地开机

## 🚀 快速开始

### 第1步：Fork 本项目到你的 GitHub

### 第2步：设置 GitHub Secrets

进入你 Fork 的仓库 → Settings → Secrets and variables → Actions → New repository secret

添加：
- `SERVERCHAN_KEY`: 你的 Server酱 SendKey

### 第3步：修改配置

编辑 `config/profile.yaml`，修改个人信息、投递方向、目标城市等

### 第4步：完成！

GitHub Actions 会在每天北京时间 9:00 自动运行，推送日报到你的微信

## 🔧 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（首次运行必须）
playwright install chromium

# 设置 Server酱 Key
export SERVERCHAN_KEY="你的SendKey"

# 运行
python main.py
```

## 📱 Server酱设置

1. 微信扫码登录 https://sct.ftqq.com/
2. 点击「SendKey」获取你的密钥
3. 将密钥设置到 GitHub Secrets 中

## 📁 项目结构

```
AutumnRecruit-AutoPush/
├── .github/
│   └── workflows/
│       └── daily.yml          # GitHub Actions 定时任务
├── config/
│   └── profile.yaml           # 个人配置（方向/城市/偏好）
├── scrapers/
│   ├── zju_scraper.py         # 浙大就业中心爬虫
│   ├── boss_scraper.py        # Boss直聘爬虫
│   ├── niuke_scraper.py       # 牛客网爬虫
│   └── guopin_scraper.py      # 国聘网爬虫
├── utils/
│   ├── jd_matcher.py          # JD匹配评分器
│   ├── push.py                # Server酱微信推送
│   └── report.py              # 日报生成器
├── reports/                   # 生成的日报（本地）
├── main.py                    # 主运行程序
├── requirements.txt           # Python依赖
└── README.md                  # 本文件
```

## ⚠️ 注意事项

- Playwright 首次运行需要下载 Chromium（~150MB），GitHub Actions 会自动处理
- 如果某个网站改版导致爬虫失效，可能需要更新对应的 scraper
- Server酱免费版每天限5条推送，足够使用
- GitHub Actions 免费额度每月2000分钟，本项目每次约3-5分钟，完全够用

## 📄 License

MIT
