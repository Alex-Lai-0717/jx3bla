# Created by moeheart at 09/27/2024
# 宋泉的定制复盘库。
# 功能待定。

from window.SpecificBossWindow import SpecificBossWindow
from replayer.boss.Base import SpecificReplayerPro
from replayer.TableConstructorMeta import TableConstructorMeta
from tools.Functions import *

import tkinter as tk
        
class SongquanWindow(SpecificBossWindow):
    '''
    宋泉的定制复盘窗口类。
    '''

    def loadWindow(self):
        '''
        使用tkinter绘制详细复盘窗口。
        '''
        self.constructWindow("宋泉", "1200x800")
        window = self.window
        
        frame1 = tk.Frame(window)
        frame1.pack()
        
        #通用格式：
        #0 ID, 1 门派, 2 有效DPS, 3 团队-心法DPS/治疗量, 4 装分, 5 详情, 6 被控时间
        
        tb = TableConstructorMeta(self.config, frame1)

        self.constructCommonHeader(tb, "")
        tb.AppendHeader("冰晶花伤害", "对冰晶花造成的总伤害量。")
        tb.AppendHeader("心法复盘", "心法专属的复盘模式，只有很少心法中有实现。")
        tb.EndOfLine()

        for i in range(len(self.effectiveDPSList)):
            line = self.effectiveDPSList[i]
            self.constructCommonLine(tb, line)

            tb.AppendContext(int(line["battle"]["binghuaDPS"]), color="#000000")

            # 心法复盘
            if line["name"] in self.occResult:
                tb.GenerateXinFaReplayButton(self.occResult[line["name"]], line["name"])
            else:
                tb.AppendContext("")
            tb.EndOfLine()

        self.constructNavigator()

    def __init__(self, config, effectiveDPSList, detail, occResult, analysedBattleData):
        super().__init__(config, effectiveDPSList, detail, occResult, analysedBattleData)

class SongquanReplayer(SpecificReplayerPro):

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

        idRemoveList = []
        for id in self.binghua:
            if self.binghua[id]["alive"] == 0 and event.time - self.binghua[id]["lastDamage"] > 500:
                time = parseTime((event.time - 500 - self.startTime) / 1000)
                self.addPot([self.bld.info.getName(self.binghua[id]["lastID"]),
                             self.occDetailList[self.binghua[id]["lastID"]],
                             0,
                             self.bossNamePrint,
                             "%s冰晶花被击破" % time,
                             self.binghua[id]["damageList"],
                             0])
                idRemoveList.append(id)
        for id in idRemoveList:
            del self.binghua[id]

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
                        if self.bld.info.getName(event.target) in ["宋泉"]:
                            self.bh.setMainTarget(event.target)
                        if self.bld.info.getName(event.target) in ["冰晶花"]:
                            self.statDict[event.caster]["battle"]["binghuaDPS"] += event.damageEff
                            if event.target not in self.binghua:
                                self.binghua[event.target] = {"lastDamage": event.time, "alive": 1, "damageList": [], "lastName": "未知"}
                            if event.damage > 0:
                                skillName = self.bld.info.getSkillName(event.full_id)
                                name = self.bld.info.getName(event.caster)
                                resultStr = ""
                                value = event.damage
                                self.binghua[event.target]["damageList"] = ["-%s, %s:%s%s(%d)" % (
                                        parseTime((int(event.time) - self.startTime) / 1000), name, skillName, resultStr, value)] + self.binghua[event.target]["damageList"]
                                if len(self.binghua[event.target]["damageList"]) > 20:
                                    del self.binghua[event.target]["damageList"][20]
                                self.binghua[event.target]["lastDamage"] = event.time
                                self.binghua[event.target]["lastID"] = event.caster

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

        elif event.dataType == "Shout":
            if event.content in ['"嘿！看我这里有很多闪闪发光的宝石，猜猜都是什么呀？"', '"嘿！看我這裡有很多閃閃發光的寶石，猜猜都是什麼呀？"']:
                self.bh.setBadPeriod(self.startTime, event.time - 1000, True, True)
            elif event.content in ['"我败了"']:
                self.win = 1
                self.bh.setBadPeriod(event.time, self.finalTime, True, True)
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
            if event.id in self.bld.info.npc and self.bld.info.npc[event.id].name in ["宋泉宝箱"]:
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
            if event.id in self.bld.info.npc and self.bld.info.npc[event.id].name in ["冰晶花"] and event.enter == 0:
                if self.binghuaTime != 0:
                    # self.bh.setBadPeriod(self.binghuaTime, event.time, True, False)
                    self.bh.setCritPeriod(self.binghuaTime - 2000, event.time, False, True)
                    self.binghuaTime = 0

        elif event.dataType == "Death":  # 重伤记录
            if event.id in self.bld.info.npc and self.bld.info.getName(event.id) in ["宋泉"]:
                self.win = 1
                self.bh.setBadPeriod(event.time, self.finalTime, True, True)
            # if event.id in self.bld.info.npc and self.bld.info.getName(event.id) in ["冰晶花"]:
            #     self.binghuaNum -= 1
            #     if self.binghuaNum == 0:
            #         self.bh.setCritPeriod(self.huaxingStart - 5000, event.time, False, True)
            #         self.huaxingStart = 0
            if event.id in self.binghua:
                self.binghua[event.id]["alive"] = 0
                self.binghua[event.id]["lastDamage"] = event.time

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
                    if event.id == "37935":
                        if self.huaxingStart == 0:
                            self.huaxingStart = event.time + 3000
                            self.binghuaNum = 3
                    if "," not in skillName:
                        key = "c%s" % event.id
                        if key in self.bhInfo or self.debug:
                            self.bh.setEnvironment(event.id, skillName, "341", event.time, 0, 1, "招式开始运功", "cast")
            if event.id == "37935":
                self.binghuaTime = event.time + 3000
            if event.caster in self.binghua and event.id == "37975":
                id = event.caster
                time = parseTime((event.time - self.startTime) / 1000)
                self.addPot([self.bld.info.getName(self.binghua[id]["lastID"]),
                             self.occDetailList[self.binghua[id]["lastID"]],
                             0,
                             self.bossNamePrint,
                             "%s冰花开始绽放" % time,
                             self.binghua[id]["damageList"].copy(),
                             0])
                    
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
        self.activeBoss = "宋泉"
        self.debug = 1

        self.initPhase(1, 1)

        self.immuneStatus = 0
        self.immuneHealer = 0
        self.immuneTime = 0

        self.bhBlackList.extend(["s37928",  # 普攻
                                 "b28861", "b28862",  # buff计数
                                 "s37931", "s37930",  # 天山剑法·引气
                                 "s37973", "s37974", "c37975",  # 天山剑法·化形
                                 "s37999", "c38457",  # 天山剑法·凝冰
                                 "s38022",  # 勾阵：水影
                                 "s38028", "s38029",  # 勾阵：普攻
                                 "s38042",  # 勾阵：冰蛇
                                 "s38073",  # 勾阵：击飞
                                 "s38087", "s38169",  # 勾阵：AOE
                                 "s38598",  # 狂暴
                                 ])
        self.bhBlackList = self.mergeBlackList(self.bhBlackList, self.config)

        self.bhInfo = {"c37929": ["16370", "#ff0000", 15000],   # 天山剑法·引气
                       "c37935": ["9535", "#ff7700", 3000],  # 天山剑法·化形
                       "c37996": ["16345", "#ff0077", 2000],  # 天山剑法·凝冰
                       "c38020": ["16380", "#ff00ff", 2000],  # 天山剑法·勾阵
                       "c38021": ["9569", "#7700ff", 5000],  # 水影
                       "c38040": ["3293", "#00ff77", 4500],  # 锁定
                       "c38041": ["4221", "#00ffff", 3000],  # 冰蛇狂舞
                       "c38086": ["3448", "#0000ff", 5000],  # 天山剑法·冰封千里
                       }

        # 宋泉数据格式：
        # ？

        # TODO cHPS

        # self.lastCuican = 0
        # self.cuicanNum = 0
        self.binghua = {}
        self.binghuaTime = 0
        self.huaxingStart = 0
        self.binghuaNum = 0

        if self.bld.info.map == "一之窟":
            self.bh.critPeriodDesc = "暂无统计"
        if self.bld.info.map == "25人普通一之窟":
            self.bh.critPeriodDesc = "[天山剑法·化形]期间，及其之前5秒."
        if self.bld.info.map == "25人英雄一之窟":
            self.bh.critPeriodDesc = "暂无统计"

        for line in self.bld.info.player:
            self.statDict[line]["battle"] = {"binghuaDPS": 0}


    def __init__(self, bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint, config):
        '''
        对类本身进行初始化。
        '''
        super().__init__(bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint)
        self.config = config

