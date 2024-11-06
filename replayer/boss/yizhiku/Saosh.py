# Created by moeheart at 09/27/2024
# 苏什的定制复盘库。
# 功能待定。

from window.SpecificBossWindow import SpecificBossWindow
from replayer.boss.Base import SpecificReplayerPro
from replayer.TableConstructorMeta import TableConstructorMeta
from tools.Functions import *

import tkinter as tk
        
class SaoshWindow(SpecificBossWindow):
    '''
    苏什的定制复盘窗口类。
    '''

    def loadWindow(self):
        '''
        使用tkinter绘制详细复盘窗口。
        '''
        self.constructWindow("苏什", "1200x800")
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

class SaoshReplayer(SpecificReplayerPro):

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

            else:
                if event.caster in self.bld.info.player and event.caster in self.statDict:
                    # self.stat[event.caster][2] += event.damageEff
                    if event.target in self.bld.info.npc:
                        if self.bld.info.getName(event.target) in ["苏什", "蘇什"]:
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
                    # if event.id in ["28050", "28052", "28054"]:
                    #     skillName = "诺布心决·指弹"
                    if "," not in skillName:
                        key = "b%s" % event.id
                        if key in self.bhInfo or self.debug:
                            self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "玩家获得气劲", "buff")

            # if event.id == "28050":  # 红宝石
            #     if event.stack == 1:
            #         self.bh.setCall("28050", "红宝石", "2654", event.time, 5000, event.target, "红宝石点名")
            #
            # if event.id == "28052":  # 蓝宝石
            #     if event.stack == 1:
            #         self.bh.setCall("28052", "蓝宝石", "2653", event.time, 5000, event.target, "蓝宝石点名")
            #
            # if event.id == "28054":  # 绿宝石
            #     if event.stack == 1:
            #         self.bh.setCall("28054", "绿宝石", "2652", event.time, 5000, event.target, "绿宝石点名")

        elif event.dataType == "Shout":
            if event.content in ['"我绝不会让你过去！"', '"我絕不會讓你過去！"']:
                self.bh.setBadPeriod(self.startTime, event.time - 1000, True, True)
            elif event.content in ['"哈维逯！到我身边！"', '"哈威逯！ 到我身邊！"']:
                self.bh.setBadPeriod(event.time, event.time + 14000, True, True)
            elif event.content in ['"为理想燃尽……亦是圆满……"', '"為理想燃盡……亦是圓滿……"']:
                self.win = 1
            elif event.content in ['"吞没大地的沙浪，你挡得住吗？"', '"吞沒大地的沙浪，你擋得住嗎？"']:
                pass
            elif event.content in ['"狂风为友，黄沙做伴！"', '"狂風為友，黃沙做伴！"']:
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
            if event.id in self.bld.info.npc and self.bld.info.getName(event.id) in ["苏什", "蘇什"]:
                self.win = 1
                self.bh.setBadPeriod(event.time, self.finalTime, True, True)

        elif event.dataType == "Battle":  # 战斗状态变化
            pass

        elif event.dataType == "Alert":  # 系统警告框
            if "小风" in event.content:
                self.bh.setEnvironment("0", event.content, "340", event.time, 0, 1, "喊话", "shout")

        elif event.dataType == "Cast":  # 施放技能事件，jcl专属
            if event.caster in self.bld.info.npc:  # 记录非玩家施放的技能
                name = "c%s" % event.id
                if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 2000:
                    self.bhTime[name] = event.time
                    skillName = self.bld.info.getSkillName(event.full_id)
                    if "," not in skillName:
                        key = "c%s" % event.id
                        if key in self.bhInfo or self.debug:
                            self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "招式开始运功", "cast")
            if event.id == "38065":
                self.bh.setCritPeriod(event.time - 1000, event.time + 10000, False, True)

                    
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
        self.activeBoss = "苏什"
        self.debug = 1

        self.initPhase(1, 1)

        self.immuneStatus = 0
        self.immuneHealer = 0
        self.immuneTime = 0

        self.bhBlackList.extend(["s38043",  # 普攻
                                 "s38045",  # 沙葬腿
                                 "s38059", "b28995", "b28997",  # 沙影钩
                                 "b28995", "s38064", "b28982",  # 狂沙噬骨掌
                                 "s38061",  # 黄沙震荡
                                 "s38051", "38049",  # 黑沙暴
                                 "s38205", "b28988",  # 种子相关
                                 "s38047", "b28995",  # 凝沙弹
                                 "s38066", "c38066",  # 飞沙走石
                                 # "b28061",  # 内伤
                                 # "c37215", "s37217", "s37220", "s37223",  # 诺布心决·指弹
                                 # "s37050", "s37072",   # 炸裂
                                 # "b28013", "b28014", "b28016",  # 力量&守护&灵动
                                 # "s37242",  # 诺布心决·璀璨
                                 # "s37193",  # 反噬
                                 # "s37210", "s37211",  # 星驰
                                 # "b28295",  # 惩罚debuff
                                 ])
        self.bhBlackList = self.mergeBlackList(self.bhBlackList, self.config)

        self.bhInfo = {"c38044": ["335", "#ff0000", 4000],   # 沙葬腿
                       "c38058": ["3312", "#ff00ff", 4000],  # 沙影钩
                       "c38063": ["279", "#0000ff", 5000],  # 狂沙噬骨掌
                       "c38060": ["3293", "#0077ff", 4000],  # 黄沙震荡
                       "c38046": ["3426", "#00ff00", 6000],  # 凝沙弹
                       "c38065": ["2022", "#7700ff", 10000],  # 飞沙走石
                       # "b28050": ["2654", "#ff0000", 5000],   # 红宝石
                       # "b28052": ["2653", "#0000ff", 5000],  # 蓝宝石
                       # "b28054": ["2652", "#00ff00", 5000],  # 绿宝石
                       # "c37229": ["9525", "#77ff77", 3000],  # 诺布心决·璀璨
                       # "c37178": ["344", "#ff0077", 10000],  # 诺布心决·炽烈
                       # "c37206": ["9527", "#ff7700", 5000],  # 诺布心决·星驰
                       # "c37454": ["9533", "#77ff00", 20000],  # 虚弱
                       }

        # 喜雅数据格式：
        # ？

        # self.lastCuican = 0
        # self.cuicanNum = 0

        if self.bld.info.map == "一之窟":
            self.bh.critPeriodDesc = "暂无统计"
        if self.bld.info.map == "25人普通一之窟":
            self.bh.critPeriodDesc = "[飞沙走石]期间."
        if self.bld.info.map == "25人英雄冷龙峰":
            self.bh.critPeriodDesc = "暂无统计"

        for line in self.bld.info.player:
            self.statDict[line]["battle"] = {}


    def __init__(self, bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint, config):
        '''
        对类本身进行初始化。
        '''
        super().__init__(bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint)
        self.config = config

