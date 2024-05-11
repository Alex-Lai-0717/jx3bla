# Created by moeheart at 03/17/2024
# 喜雅的定制复盘库。
# 功能待定。

from window.SpecificBossWindow import SpecificBossWindow
from replayer.boss.Base import SpecificReplayerPro
from replayer.TableConstructorMeta import TableConstructorMeta
from tools.Functions import *

import tkinter as tk
        
class XiYaWindow(SpecificBossWindow):
    '''
    喜雅的定制复盘窗口类。
    '''

    def loadWindow(self):
        '''
        使用tkinter绘制详细复盘窗口。
        '''
        self.constructWindow("喜雅", "1200x800")
        window = self.window
        
        frame1 = tk.Frame(window)
        frame1.pack()
        
        #通用格式：
        #0 ID, 1 门派, 2 有效DPS, 3 团队-心法DPS/治疗量, 4 装分, 5 详情, 6 被控时间
        
        tb = TableConstructorMeta(self.config, frame1)

        self.constructCommonHeader(tb, "")
        # tb.AppendHeader("1组剑", "对第1组剑的伤害量，红/蓝表示不同的分组。如果剑没有打掉，则会显示为浅色。")
        tb.AppendHeader("心法复盘", "心法专属的复盘模式，只有很少心法中有实现。")
        tb.EndOfLine()

        for i in range(len(self.effectiveDPSList)):
            line = self.effectiveDPSList[i]
            self.constructCommonLine(tb, line)

            # 心法复盘
            if line["name"] in self.occResult:
                tb.GenerateXinFaReplayButton(self.occResult[line["name"]], line["name"])
            else:
                tb.AppendContext("")
            tb.EndOfLine()

        self.constructNavigator()

    def __init__(self, config, effectiveDPSList, detail, occResult, analysedBattleData):
        super().__init__(config, effectiveDPSList, detail, occResult, analysedBattleData)

class XiYaReplayer(SpecificReplayerPro):

    def countFinal(self):
        '''
        战斗结束时需要处理的流程。包括BOSS的通关喊话和全团脱战。
        '''

        self.countFinalOverall()
        self.changePhase(self.finalTime, 0)
        self.bh.setEnvironmentInfo(self.bhInfo)
        self.bh.printEnvironmentInfo()
        # print(self.bh.log)

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

                if event.id == "37242" and event.time - self.lastCuican > 10000:
                    self.lastCuican = event.time
                    self.cuicanNum += 1
                    if self.bld.info.map != "25人英雄冷龙峰":
                        self.bh.setCritPeriod(event.time - 5000, event.time + 400, False, True)
                    elif self.cuicanNum == 3:
                        self.bh.setCritPeriod(event.time - 5000, self.finalTime, False, True)

            else:
                if event.caster in self.bld.info.player and event.caster in self.statDict:
                    # self.stat[event.caster][2] += event.damageEff
                    if event.target in self.bld.info.npc:
                        if self.bld.info.getName(event.target) in ["喜雅"]:
                            self.bh.setMainTarget(event.target)

        elif event.dataType == "Buff":
            if event.target not in self.bld.info.player:
                return

            if event.caster in self.bld.info.npc and event.stack > 0:
                # 尝试记录buff事件
                name = "b%s" % event.id
                if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 5000:
                    self.bhTime[name] = event.time
                    skillName = self.bld.info.getSkillName(event.full_id)
                    if event.id in ["28050", "28052", "28054"]:
                        skillName = "诺布心决·指弹"
                    if "," not in skillName:
                        key = "b%s" % event.id
                        if key in self.bhInfo or self.debug:
                            self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "玩家获得气劲", "buff")

            if event.id == "28050":  # 红宝石
                if event.stack == 1:
                    self.bh.setCall("28050", "红宝石", "2654", event.time, 5000, event.target, "红宝石点名")

            if event.id == "28052":  # 蓝宝石
                if event.stack == 1:
                    self.bh.setCall("28052", "蓝宝石", "2653", event.time, 5000, event.target, "蓝宝石点名")

            if event.id == "28054":  # 绿宝石
                if event.stack == 1:
                    self.bh.setCall("28054", "绿宝石", "2652", event.time, 5000, event.target, "绿宝石点名")

        elif event.dataType == "Shout":
            if event.content in ['"嘿！看我这里有很多闪闪发光的宝石，猜猜都是什么呀？"', '"嘿！看我這裡有很多閃閃發光的寶石，猜猜都是什麼呀？"']:
                self.bh.setBadPeriod(self.startTime, event.time - 1000, True, True)
            elif event.content in ['"看我的宝石，咻！"', '"看我的寶石，咻！"']:
                pass
            elif event.content in ['"用所有的宝石……创造美丽的烟花吧！"', '"用所有的寶石…創造美麗的煙花吧！"']:
                pass
            elif event.content in ['"呼呼！停……让我休息会儿。"', '"呼呼！停…讓我休息會兒。"']:
                pass
            elif event.content in ['"小心哦！这枚宝石比天上的星星更绚烂！"', '"小心哦！這枚寶石比天上的星星更絢爛！"']:
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
            elif event.content in ['""']:
                pass
            else:
                self.bh.setEnvironment("0", event.content, "341", event.time, 0, 1, "喊话", "shout")

        elif event.dataType == "Scene":  # 进入、离开场景
            if event.id in self.bld.info.npc and self.bld.info.npc[event.id].name in ["喜雅宝箱", "喜雅寶箱", "鹰眼客", "鷹眼客"]:
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

        elif event.dataType == "Death":  # 重伤记录
            if event.id in self.bld.info.npc and self.bld.info.getName(event.id) in ["喜雅"]:
                self.win = 1
                self.bh.setBadPeriod(event.time, self.finalTime, True, True)

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
        self.activeBoss = "喜雅"
        self.debug = 1

        self.initPhase(1, 1)

        self.immuneStatus = 0
        self.immuneHealer = 0
        self.immuneTime = 0

        self.bhBlackList.extend(["b28061",  # 内伤
                                 "c37215", "s37217", "s37220", "s37223",  # 诺布心决·指弹
                                 "s37050", "s37072",   # 炸裂
                                 "b28013", "b28014", "b28016",  # 力量&守护&灵动
                                 "s37242",  # 诺布心决·璀璨
                                 "s37193",  # 反噬
                                 "s37210", "s37211",  # 星驰
                                 "b28295",  # 惩罚debuff
                                 ])
        self.bhBlackList = self.mergeBlackList(self.bhBlackList, self.config)

        self.bhInfo = {"b28050": ["2654", "#ff0000", 5000],   # 红宝石
                       "b28052": ["2653", "#0000ff", 5000],  # 蓝宝石
                       "b28054": ["2652", "#00ff00", 5000],  # 绿宝石
                       "c37229": ["9525", "#77ff77", 3000],  # 诺布心决·璀璨
                       "c37178": ["344", "#ff0077", 10000],  # 诺布心决·炽烈
                       "c37206": ["9527", "#ff7700", 5000],  # 诺布心决·星驰
                       "c37454": ["9533", "#77ff00", 20000],  # 虚弱
                       }

        # 喜雅数据格式：
        # ？

        self.lastCuican = 0
        self.cuicanNum = 0

        if self.bld.info.map == "冷龙峰":
            self.bh.critPeriodDesc = "从每次[诺布心决·璀璨]之前5秒开始，到0.4秒后三连AOE结束"
        if self.bld.info.map == "25人普通冷龙峰":
            self.bh.critPeriodDesc = "从每次[诺布心决·璀璨]之前5秒开始，到0.4秒后三连AOE结束"
        if self.bld.info.map == "25人英雄冷龙峰":
            self.bh.critPeriodDesc = "从第三次[诺布心决·璀璨]开始，到整个战斗结束"

        for line in self.bld.info.player:
            self.statDict[line]["battle"] = {}


    def __init__(self, bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint, config):
        '''
        对类本身进行初始化。
        '''
        super().__init__(bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint)
        self.config = config

