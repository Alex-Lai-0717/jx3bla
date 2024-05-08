# Created by moeheart at 03/17/2024
# 雨轻红的定制复盘库。
# 功能待定。

from window.SpecificBossWindow import SpecificBossWindow
from replayer.boss.Base import SpecificReplayerPro
from replayer.TableConstructorMeta import TableConstructorMeta
from tools.Functions import *

import tkinter as tk
        
class YuQinghongWindow(SpecificBossWindow):
    '''
    雨轻红的定制复盘窗口类。
    '''

    def loadWindow(self):
        '''
        使用tkinter绘制详细复盘窗口。
        '''
        self.constructWindow("雨轻红", "1200x800")
        window = self.window
        
        frame1 = tk.Frame(window)
        frame1.pack()
        
        #通用格式：
        #0 ID, 1 门派, 2 有效DPS, 3 团队-心法DPS/治疗量, 4 装分, 5 详情, 6 被控时间
        
        tb = TableConstructorMeta(self.config, frame1)

        self.constructCommonHeader(tb, "")
        tb.AppendHeader("梦蝶伤害", "对梦蝶造成的总伤害量。")
        tb.AppendHeader("蝶雨次数", "被[炼红脂·蝶雨]命中的次数")
        tb.AppendHeader("心法复盘", "心法专属的复盘模式，只有很少心法中有实现。")
        tb.EndOfLine()

        for i in range(len(self.effectiveDPSList)):
            line = self.effectiveDPSList[i]
            self.constructCommonLine(tb, line)

            tb.AppendContext(int(line["battle"]["mengdieDPS"]), color="#000000")
            tb.AppendContext(int(line["battle"]["dieyuNum"]), color="#000000")

            # 心法复盘
            if line["name"] in self.occResult:
                tb.GenerateXinFaReplayButton(self.occResult[line["name"]], line["name"])
            else:
                tb.AppendContext("")
            tb.EndOfLine()

        self.constructNavigator()

    def __init__(self, config, effectiveDPSList, detail, occResult, analysedBattleData):
        super().__init__(config, effectiveDPSList, detail, occResult, analysedBattleData)

class YuQinghongReplayer(SpecificReplayerPro):

    def countFinal(self):
        '''
        战斗结束时需要处理的流程。包括BOSS的通关喊话和全团脱战。
        '''

        self.countFinalOverall()
        self.changePhase(self.finalTime, 0)
        self.bh.setEnvironmentInfo(self.bhInfo)
        self.bh.printEnvironmentInfo()
        # print(self.bh.log)

        # 有时BOSS会没有任何通关标记，用血量做一个兜底判定
        if self.totalDamage > self.bossHP * 0.99:
            self.win = 1

    def getResult(self):
        '''
        生成复盘结果的流程。需要维护effectiveDPSList, potList与detail。
        '''

        self.countFinal()

        bossResult = []
        for id in self.bld.info.player:
            if id in self.statDict:
                res = self.getBaseList(id)
                bossResult.append(res)
        self.statList = bossResult

        return self.statList, self.potList, self.detail, self.stunCounter

    def recordDeath(self, item, deathSource):
        '''
        在有玩家重伤时的额外代码。
        params
        - item 复盘数据，意义同茗伊复盘。
        - deathSource 重伤来源。
        '''
        pass

    def analyseSecondStage(self, event):
        '''
        处理单条复盘数据时的流程，在第二阶段复盘时，会以时间顺序不断调用此方法。
        params
        - item 复盘数据，意义同茗伊复盘。
        '''

        self.checkTimer(event.time)

        idRemoveList = []
        for id in self.mengdie:
            if self.mengdie[id]["alive"] == 0 and event.time - self.mengdie[id]["lastDamage"] > 500:
                time = parseTime((event.time - 500 - self.startTime) / 1000)
                self.addPot([self.bld.info.getName(self.mengdie[id]["lastID"]),
                             self.occDetailList[self.mengdie[id]["lastID"]],
                             0,
                             self.bossNamePrint,
                             "%s梦蝶被击破" % time,
                             self.mengdie[id]["damageList"],
                             0])
                idRemoveList.append(id)
        for id in idRemoveList:
            del self.mengdie[id]

        if event.dataType == "Skill":
            if event.target in self.bld.info.player:
                if event.heal > 0 and event.effect != 7 and event.caster in self.hps:  # 非化解
                    self.hps[event.caster] += event.healEff

                if event.caster in self.bld.info.npc and event.heal == 0 and event.scheme == 1:
                    # 尝试记录技能事件
                    name = "s%s" % event.id
                    if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 3000:
                        self.bhTime[name] = event.time
                        skillName = self.bld.info.getSkillName(event.full_id)
                        if "," not in skillName:
                            key = "s%s" % event.id
                            if key in self.bhInfo or self.debug:
                                self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "招式命中玩家", "skill")

                if event.id == "36974":
                    self.statDict[event.target]["battle"]["dieyuNum"] += 1

            else:
                if event.caster in self.bld.info.player and event.caster in self.statDict:
                    # self.stat[event.caster][2] += event.damageEff
                    if event.target in self.bld.info.npc:
                        if self.bld.info.getName(event.target) in ["雨轻红", "雨輕紅"]:
                            self.bh.setMainTarget(event.target)
                            self.totalDamage += event.damageEff
                        if self.bld.info.getName(event.target) in ["梦蝶", "夢蝶"]:
                            self.statDict[event.caster]["battle"]["mengdieDPS"] += event.damageEff
                            if event.target not in self.mengdie:
                                self.mengdie[event.target] = {"lastDamage": event.time, "alive": 1, "damageList": [], "lastName": "未知"}
                            if event.damage > 0:
                                skillName = self.bld.info.getSkillName(event.full_id)
                                name = self.bld.info.getName(event.caster)
                                resultStr = ""
                                value = event.damage
                                self.mengdie[event.target]["damageList"] = ["-%s, %s:%s%s(%d)" % (
                                        parseTime((int(event.time) - self.startTime) / 1000), name, skillName, resultStr, value)] + self.mengdie[event.target]["damageList"]
                                if len(self.mengdie[event.target]["damageList"]) > 20:
                                    del self.mengdie[event.target]["damageList"][20]
                                self.mengdie[event.target]["lastDamage"] = event.time
                                self.mengdie[event.target]["lastID"] = event.caster

        elif event.dataType == "Buff":
            if event.target not in self.bld.info.player:
                return

            if event.caster in self.bld.info.npc and event.stack > 0:
                # 尝试记录buff事件
                name = "b%s" % event.id
                if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 10000:
                    self.bhTime[name] = event.time
                    skillName = self.bld.info.getSkillName(event.full_id)
                    if "," not in skillName:
                        key = "b%s" % event.id
                        if key in self.bhInfo or self.debug:
                            self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "玩家获得气劲", "buff")

        elif event.dataType == "Shout":
            if event.content in ['"呵……有多少人情愿沉沦长梦而不得，你又何必挣扎清醒？"']:
                pass
            elif event.content in ['"香风飘散。"']:
                pass
            elif event.content in ['"蝴蝶的飞舞，让深陷其中者无法自拔。"']:
                pass
            elif event.content in ['"沐浴在迷雾之中吧。"']:
                pass
            elif event.content in ['"潮起潮落，你的生死只在一线之间。"']:
                pass
            elif event.content in ['"沉浸在我的梦魇之中，陷入无尽的恐惧与迷离吧！"']:
                pass
            elif event.content in ['""']:
                pass
            elif event.content in ['""']:
                pass
            elif event.content in ['""']:
                pass
            elif event.content in ['""']:
                pass
            elif event.content in ['""']:
                pass
            elif event.content in ['""']:
                pass
            else:
                self.bh.setEnvironment("0", event.content, "341", event.time, 0, 1, "喊话", "shout")

        elif event.dataType == "Scene":  # 进入、离开场景
            if event.id in self.bld.info.npc and self.bld.info.npc[event.id].name in ["雨轻红宝箱", "雨輕紅寶箱"]:
                self.win = 1
                self.bh.setBadPeriod(event.time, self.finalTime, True, True)
            if event.id in self.bld.info.npc and event.enter and self.bld.info.npc[event.id].name != "":
                name = "n%s" % self.bld.info.npc[event.id].templateID
                skillName = self.bld.info.npc[event.id].name
                if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 3000:
                    self.bhTime[name] = event.time
                    if "的" not in skillName:
                        key = "n%s" % self.bld.info.npc[event.id].templateID
                        # if key in self.bhInfo or self.debug:
                        #     self.bh.setEnvironment(self.bld.info.npc[event.id].templateID, skillName, "341", event.time, 0,
                        #                        1, "NPC出现", "npc")

            if event.id in self.bld.info.npc and self.bld.info.npc[event.id].name in ["梦蝶", "夢蝶"] and event.enter == 0:
                if self.mengdieTime != 0:
                    self.bh.setBadPeriod(self.mengdieTime, event.time, True, False)
                    self.bh.setCritPeriod(self.mengdieTime - 2000, event.time, False, True)
                    self.mengdieTime = 0

        elif event.dataType == "Death":  # 重伤记录
            if event.id in self.bld.info.npc and self.bld.info.getName(event.id) in ["雨轻红", "雨輕紅"]:
                self.win = 1
                self.bh.setBadPeriod(event.time, self.finalTime, True, True)
            if event.id in self.mengdie:
                self.mengdie[event.id]["alive"] = 0
                self.mengdie[event.id]["lastDamage"] = event.time

        elif event.dataType == "Battle":  # 战斗状态变化
            pass

        elif event.dataType == "Alert":  # 系统警告框
            pass

        elif event.dataType == "Cast":  # 施放技能事件，jcl专属
            if event.caster in self.bld.info.npc:  # 记录非玩家施放的技能
                name = "c%s" % event.id
                if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 2000:
                    self.bhTime[name] = event.time
                    skillName = self.bld.info.getSkillName(event.full_id)
                    if "," not in skillName:
                        self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "招式开始运功", "cast")
            if event.caster in self.mengdie and event.id == "36994":
                id = event.caster
                time = parseTime((event.time - self.startTime) / 1000)
                self.addPot([self.bld.info.getName(self.mengdie[id]["lastID"]),
                             self.occDetailList[self.mengdie[id]["lastID"]],
                             0,
                             self.bossNamePrint,
                             "%s梦蝶开始唤醒" % time,
                             self.mengdie[id]["damageList"].copy(),
                             0])
            if event.id == "37017":  # 蝶雨
                if event.level == 1:
                    self.bh.setBadPeriod(event.time, event.time + 10000, True, True)
                else:
                    self.bh.setBadPeriod(event.time, event.time + 20000, True, True)

                if self.bld.info.map == "冷龙峰":
                    self.bh.setCritPeriod(event.time - 5000, event.time + 10000, False, True)
                elif self.bld.info.map == "25人普通冷龙峰":
                    self.bh.setCritPeriod(event.time - 5000, event.time + 20000, False, True)

            if event.id == "36987":  # 柔梦
                self.mengdieTime = event.time + 3000  # 读条结束的时间

                    
    def analyseFirstStage(self, item):
        '''
        处理单条复盘数据时的流程，在第一阶段复盘时，会以时间顺序不断调用此方法。
        params
        - item 复盘数据，意义同茗伊复盘。
        '''
        pass

    def initBattle(self):
        '''
        在战斗开始时的初始化流程，当第二阶段复盘开始时运行。
        '''
        self.initBattleBase()
        self.activeBoss = "雨轻红"
        self.debug = 1

        self.initPhase(1, 1)

        self.immuneStatus = 0
        self.immuneHealer = 0
        self.immuneTime = 0

        self.bhBlackList.extend(["s36925", "b27872", "s36926", "s37271",  # 炼红脂·迷雾
                                 "s36974",  # 炼红脂·蝶雨
                                 "s36935", "b27878",  # 炼红脂·香风
                                 "s36983", "s36984", "s36985", "s37188",  # 炼红脂·归潮
                                 "s36928",  # 掉落传送
                                 "s36988", "s37021",  # 炼红脂·柔梦:梦魇-扇形
                                 "c36994",  # 唤醒

                                 ])
        self.bhBlackList = self.mergeBlackList(self.bhBlackList, self.config)

        self.bhInfo = {"c36920": ["9567", "#0000ff", 2000],   # 炼红脂·迷雾
                       "c36932": ["9557", "#00ff00", 2000],  # 炼红脂·香风
                       "c36972": ["9543", "#ff0000", 5000],  # 炼红脂·蝶雨
                       "c37017": ["9543", "#ff0000", 20000],  # 炼红脂·蝶雨
                       "c36982": ["9562", "#007700", 3000],  # 炼红脂·归潮
                       "c36987": ["9544", "#ff7777", 3000],  # 炼红脂·柔梦
                       "c37022": ["4547", "#ff0077", 5000],  # 炼红脂·柔梦
                       }

        self.mengdie = {}
        self.totalDamage = 0
        self.bossHP = 787500000

        self.mengdieTime = 0

        if self.bld.info.map == "冷龙峰":
            self.bhInfo["c37017"] = ["9543", "#ff0000", 10000]
            self.bh.critPeriodDesc = "从每次[炼红脂·蝶雨]之前5秒开始，到10秒读条结束"
        if self.bld.info.map == "25人普通冷龙峰":
            self.bossHP = 2590000000
            self.bh.critPeriodDesc = "从每次[炼红脂·蝶雨]之前5秒开始，到20秒读条结束"
        if self.bld.info.map == "25人英雄冷龙峰":
            self.bossHP = 4121600000
            self.bh.critPeriodDesc = "从每次[炼红脂·柔梦]之前5秒开始，到柔梦阶段结束"

        # 雨轻红数据格式：
        # 梦蝶DPS，蝶雨次数

        for line in self.bld.info.player:
            self.statDict[line]["battle"] = {"mengdieDPS": 0,
                                             "dieyuNum": 0,
                                             }


    def __init__(self, bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint, config):
        '''
        对类本身进行初始化。
        '''
        super().__init__(bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint)
        self.config = config

