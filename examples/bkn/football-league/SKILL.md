# 足球联赛知识网络 - Agent 使用指南

> **网络ID**: football_league
> **标签**: 足球, 联赛, 体育

## 网络概览

本知识网络建模足球联赛的核心实体与关系，涵盖联赛、球队、球员、比赛、进球五大对象，
支持赛事管理、球员转会、战术分析、纪律处罚等场景。

### 核心对象

| 对象 | 文件路径 | 说明 |
|------|----------|------|
| 联赛 | `object_types/league.bkn` | 足球联赛赛事（英超、西甲、中超等） |
| 球队 | `object_types/team.bkn` | 职业足球俱乐部 |
| 球员 | `object_types/player.bkn` | 职业足球运动员 |
| 比赛 | `object_types/match.bkn` | 联赛中的单场比赛 |
| 进球 | `object_types/goal.bkn` | 比赛中的进球记录 |

### 核心关系

| 关系 | 文件路径 | 源 → 目标 | 说明 |
|------|----------|-----------|------|
| team_in_league | `relation_types/team_in_league.bkn` | 球队 → 联赛 | 球队参加联赛 |
| player_belongs_team | `relation_types/player_belongs_team.bkn` | 球员 → 球队 | 球员效力球队 |
| match_home_team | `relation_types/match_home_team.bkn` | 比赛 → 球队 | 比赛主队 |
| match_away_team | `relation_types/match_away_team.bkn` | 比赛 → 球队 | 比赛客队 |
| goal_scored_by | `relation_types/goal_scored_by.bkn` | 进球 → 球员 | 进球由球员打入 |

### 可用行动

| 行动 | 文件路径 | 绑定对象 | 说明 |
|------|----------|----------|------|
| transfer_player | `action_types/transfer_player.bkn` | 球员 | 球员转会 |
| suspend_player | `action_types/suspend_player.bkn` | 球员 | 球员停赛处罚 |

## 拓扑关系

```
联赛 (league)
 └── 球队 (team)        ← team_in_league
      └── 球员 (player) ← player_belongs_team
           └── 进球 (goal) ← goal_scored_by
比赛 (match)
 ├── 主队 (team)        ← match_home_team
 └── 客队 (team)        ← match_away_team
```

## 使用场景

### 查询场景

1. **查看联赛球队** — 查询 `team` 对象，按 `league_id` 过滤
2. **球队阵容** — 查询 `player` 对象，按 `team_id` 过滤
3. **比赛结果** — 查询 `match` 对象，按 `round` 或 `match_date` 过滤
4. **射手榜** — 通过 `goal` + `goal_scored_by` 关系聚合球员进球数

### 运维场景

1. **球员转会** — 读取 `action_types/transfer_player.bkn`，执行转会行动
2. **纪律处罚** — 读取 `action_types/suspend_player.bkn`，执行停赛处罚

## 索引

- **对象定义**: `object_types/*.bkn`
- **关系定义**: `relation_types/*.bkn`
- **行动定义**: `action_types/*.bkn`
- **概念分组**: `concept_groups/*.bkn`
