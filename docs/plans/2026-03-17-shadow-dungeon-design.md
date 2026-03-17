# 暗影地牢 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重写一个可在网页端和手机端运行、可部署到 GitHub Pages 的高可玩性 roguelike，重点提升战斗手感。

**Architecture:** 单文件 `index.html`，使用 Canvas 2D 渲染、回合制逻辑与动画队列分离。核心状态机分为标题/职业选择/运行中/背包/商店/死亡/胜利，战斗反馈通过浮字、震屏、粒子、闪白、延迟血条实现。

**Tech Stack:** HTML + CSS + Vanilla JavaScript（无外部依赖）

---

### Task 1: 基础框架与状态机
### Task 2: 地图与实体系统
### Task 3: 战斗与手感系统（重点）
### Task 4: 成长系统与装备词缀
### Task 5: Boss 与随机事件
### Task 6: 控制与部署准备
