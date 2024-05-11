# Created by moeheart at 03/17/2024
# 赤幽明的定制复盘库。
# 功能待定。

from window.SpecificBossWindow import SpecificBossWindow
from replayer.boss.Base import SpecificReplayerPro
from replayer.TableConstructorMeta import TableConstructorMeta
from tools.Functions import *

import tkinter as tk
        
class ChiYoumingWindow(SpecificBossWindow):
    '''
    赤幽明的定制复盘窗口类。
    '''

    def loadWindow(self):
        '''
        使用tkinter绘制详细复盘窗口。
        '''
        self.constructWindow("赤幽明", "1200x800")
        window = self.window
        
        frame1 = tk.Frame(window)
        frame1.pack()
        
        #通用格式：
        #0 ID, 1 门派, 2 有效DPS, 3 团队-心法DPS/治疗量, 4 装分, 5 详情, 6 被控时间
        
        tb = TableConstructorMeta(self.config, frame1)

        self.constructCommonHeader(tb, "")

        tb.AppendHeader("P1DPS", "对P1[赤幽明]的DPS。\n阶段持续时间：%s" % parseTime(self.detail["P1Time"]))
        tb.AppendHeader("P2DPS", "对P2[赤幽明]的DPS。\n阶段持续时间：%s" % parseTime(self.detail["P1Time"]))
        tb.AppendHeader("倒影伤害", "对[血凝黑镜]产生的[倒影]的伤害。")
        tb.AppendHeader("群攻黑影伤害", "在P2，对[真神光耀]之后产生的[游荡黑影]的伤害。这个伤害一般由群攻产生。")
        tb.AppendHeader("单体黑影伤害", "在P2，对[旋转火刀]之后产生的[游荡黑影]的伤害。这个伤害一般由单体产生。")
        tb.EndOfLine()

        for i in range(len(self.effectiveDPSList)):
            line = self.effectiveDPSList[i]
            self.constructCommonLine(tb, line)

            tb.AppendContext(int(line["battle"]["P1DPS"]))
            tb.AppendContext(int(line["battle"]["P2DPS"]))
            tb.AppendContext(int(line["battle"]["daoyingDPS"]))
            tb.AppendContext(int(line["battle"]["heiyingDPS1"]))
            tb.AppendContext(int(line["battle"]["heiyingDPS2"]))

            # 心法复盘
            if line["name"] in self.occResult:
                tb.GenerateXinFaReplayButton(self.occResult[line["name"]], line["name"])
            else:
                tb.AppendContext("")
            tb.EndOfLine()

        self.constructNavigator()

    def __init__(self, config, effectiveDPSList, detail, occResult, analysedBattleData):
        super().__init__(config, effectiveDPSList, detail, occResult, analysedBattleData)

class ChiYoumingReplayer(SpecificReplayerPro):

    def countFinal(self):
        '''
        战斗结束时需要处理的流程。包括BOSS的通关喊话和全团脱战。
        '''

        self.countFinalOverall()
        self.changePhase(self.finalTime, 0)
        self.bh.setEnvironmentInfo(self.bhInfo)
        self.bh.printEnvironmentInfo()
        # print(self.bh.log)

        self.detail["P1Time"] = int(self.phaseTime[1] / 1000)
        self.detail["P2Time"] = int(self.phaseTime[2] / 1000)

    def getResult(self):
        '''
        生成复盘结果的流程。需要维护effectiveDPSList, potList与detail。
        '''

        self.countFinal()

        bossResult = []
        for id in self.bld.info.player:
            if id in self.statDict:
                res = self.getBaseList(id)
                res["battle"]["P1DPS"] = int(safe_divide(res["battle"]["P1DPS"], self.detail["P1Time"]))
                res["battle"]["P2DPS"] = int(safe_divide(res["battle"]["P2DPS"], self.detail["P2Time"]))
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

                if event.id == "37002" and event.time - self.lastHuodaoEnd > 1000:  # 旋转火刀震爆
                    self.lastHuodaoEnd = event.time
                    self.bh.setCritPeriod(event.time - 5000, event.time, False, True)
                    if self.lastHuodaoStart != 0:
                        self.bh.setBadPeriod(self.lastHuodaoStart, event.time, True, False)
                        self.lastHuodaoStart = 0

            else:
                if event.caster in self.bld.info.player and event.caster in self.statDict:
                    # self.stat[event.caster][2] += event.damageEff
                    if event.target in self.bld.info.npc:
                        if self.bld.info.getName(event.target) in ["赤幽明"]:
                            self.bh.setMainTarget(event.target)
                            if self.phase == 1:
                                self.statDict[event.caster]["battle"]["P1DPS"] += event.damageEff
                            elif self.phase == 2:
                                self.statDict[event.caster]["battle"]["P2DPS"] += event.damageEff
                        if self.bld.info.getName(event.target) in ["倒影"]:
                            self.statDict[event.caster]["battle"]["daoyingDPS"] += event.damageEff
                        if self.bld.info.getName(event.target) in ["游荡黑影", "遊蕩黑影"]:
                            if self.heiying.get(event.target, 0) == 1:
                                self.statDict[event.caster]["battle"]["heiyingDPS1"] += event.damageEff
                            elif self.heiying.get(event.target, 0) == 2:
                                self.statDict[event.caster]["battle"]["heiyingDPS2"] += event.damageEff
                    # if self.bld.info.getName(event.caster) == "解雨笺·梦江南" and event.damageEff > 0:
                    #     print("[heiyingTest]", self.statDict[event.caster]["battle"]["heiyingDPS1"], event.time, event.damageEff, self.heiying.get(event.target, 0), self.bld.info.getName(event.caster), self.bld.info.getName(event.target), self.bld.info.getSkillName(event.full_id), parseTime((event.time - self.startTime) / 1000))

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
            if event.content in ['"来吧！以阿胡拉之名，击败你们这些妖孽！"', '"來吧！以阿胡拉之名，擊敗你們這些妖孽！"']:
                self.bh.setBadPeriod(self.startTime, event.time - 1000, True, True)
            elif event.content in ['"好好感受陷入深渊的感觉吧……"', '"好好感受陷入深淵的感覺吧…"']:
                self.bh.setEnvironment("0", "漆黑泥沼", "12449", event.time, 0, 1, "喊话", "shout")
            elif event.content in ['"怎么可能……亵渎之人，神必将你们焚烧殆尽……"', ''"怎麼可能…褻瀆之人，神必將你們焚燒殆盡…"]:
                self.win = 1
            elif event.content in ['"以烈火和熔铁，对灵魂做出判决！"', '"以烈火和熔鐵，對靈魂做出判決！"']:
                pass
            elif event.content in ['"我来抓你咯……渎神者。"', '"我來抓你咯…瀆神者。"']:
                self.bh.setEnvironment("0", "游荡黑影", "3432", event.time, 0, 1, "喊话", "shout")
            elif event.content in ['"照照你们的丑陋嘴脸吧！"', '"照照你們的醜陋嘴臉吧！"']:
                self.bh.setEnvironment("0", "黑镜", "4547", event.time, 0, 1, "喊话", "shout")
            elif event.content in ['"没有信仰的人，只有死路一条！"', '"沒有信仰的人，只有死路一條！"']:
                pass
            elif event.content in ['"闪耀着灵光的众灵体啊，放射出刺眼的光芒吧！"', '"閃耀著靈光的眾靈體啊，放射出刺眼的光芒吧！"']:
                pass
            elif event.content in ['"嘿嘿嘿嘿……"', '"嘿嘿嘿嘿……"']:
                pass
            elif event.content in ['"啊，威严的、光辉灿烂的阿胡拉·马兹达！指引我的方向吧！"', '"啊，威嚴的、光輝燦爛的阿胡拉·馬茲達！指引我的方向吧！"']:
                pass
            elif event.content in ['"喝啊！"', '"喝啊！"']:
                pass
            elif event.content in ['"住手！"', '"住手！"']:
                pass
            elif event.content in ['"你还好吗？没料到你身处险境。"', '"你還好嗎？沒料到你身處險境。"']:
                pass
            elif event.content in ['"呃……"', '"呃…"']:
                self.changePhase(event.time, 0)
            elif event.content in ['"威严的、光辉灿烂的阿胡拉·马兹达！我祈求取之不尽，用之不竭的力量和压倒一切的优势……赐予我的哥哥。"', '"威嚴的、光輝燦爛的阿胡拉·馬茲達！我祈求取之不盡，用之不竭的力量和壓倒一切的優勢……賜予我的哥哥。"']:
                pass
            elif event.content in ['"啊……"', '"啊…"']:
                pass
            elif event.content in ['"我，在此申明！我崇拜马兹达！追随琐罗亚斯德！是众妖魔的敌人和祆教的信徒！"', '"我，在此申明！我崇拜馬茲達！追隨瑣羅亞斯德！是眾妖魔的敵人和祆教的信徒！"']:
                self.bh.setBadPeriod(self.phaseStart, event.time, True, True)
                self.changePhase(event.time, 2)
            elif event.content in ['"啊……伟大的马兹达！快来庇佑我吧！庇佑我一千次！庇佑我一万次！"', '"啊…偉大的馬茲達！快來庇佑我吧！庇佑我一千次！庇佑我一萬次！"']:
                pass
            elif event.content in ['"渎神者必将沉没于黑暗中！"', '"瀆神者必將沉沒於黑暗中！"']:
                self.bh.setEnvironment("0", "漆黑泥沼·P2", "12449", event.time, 0, 1, "喊话", "shout")
            elif event.content in ['"让黑暗的帷幕在火焰中焚灼！"', '"讓黑暗的帷幕在火焰中焚燒！"']:
                self.lastHuodao = event.time
            elif event.content in ['"住手！"']:
                pass
            elif event.content in ['"住手！"']:
                pass
            elif event.content in ['"住手！"']:
                pass
            else:
                self.bh.setEnvironment("0", event.content, "341", event.time, 0, 1, "喊话", "shout")

        elif event.dataType == "Scene":  # 进入、离开场景
            # if event.id in self.bld.info.npc and self.bld.info.npc[event.id].name in ["翁幼之宝箱", "??寶箱"]:
            #     self.win = 1
            #     self.bh.setBadPeriod(event.time, self.finalTime, True, True)
            if event.id in self.bld.info.npc and event.enter and self.bld.info.npc[event.id].name != "":
                name = "n%s" % self.bld.info.npc[event.id].templateID
                skillName = self.bld.info.npc[event.id].name
                if name not in self.bhBlackList and event.time - self.bhTime.get(name, 0) > 3000:
                    self.bhTime[name] = event.time
                    if "的" not in skillName:
                        key = "n%s" % self.bld.info.npc[event.id].templateID
                        if key in self.bhInfo:
                            self.bh.setEnvironment(self.bld.info.npc[event.id].templateID, skillName, "341", event.time, 0,
                                               1, "NPC出现", "npc")
            if event.id in self.bld.info.npc and event.enter and self.bld.info.npc[event.id].name in ["游荡黑影", "遊蕩黑影"]:
                if event.id not in self.heiying:
                    if event.time - self.lastHuodao > 10000:
                        self.heiying[event.id] = 1
                    else:
                        self.heiying[event.id] = 2

        elif event.dataType == "Death":  # 重伤记录
            pass

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

            if event.id == "36999":  # 旋转火刀
                self.lastHuodaoStart = event.time
                    
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
        self.activeBoss = "赤幽明"
        self.debug = 1

        self.initPhase(2, 1)

        self.immuneStatus = 0
        self.immuneHealer = 0
        self.immuneTime = 0

        self.bhBlackList.extend(["s37010", "s36995", "s37011", "b28064", "b27945", "s37539"  # 普攻
                                 "b27946", "s37008",  # 漆黑泥沼
                                 "b27953", "c37208", "s37001", "b27934", "s37002",  # 旋转火刀
                                 "s37013", "b27937",  # 旋转火刀·P2
                                 "s36997", "b27926", "s37036",  # 熔铁利刃
                                 "s37004", "s37015",  # 真神光耀
                                 "b27952", "s36998",  # 初窥灵光
                                 "s37212",  # 倒影普攻
                                 "b28267",  # 黑镜
                                 "s37129", "b28137",   # 游荡黑影
                                 "s37014", "s37041",   # 恶毒利刃
                                 "c37530",  # 结束剧情
                                 ])
        self.bhBlackList = self.mergeBlackList(self.bhBlackList, self.config)

        self.bhInfo = {"c37004": ["2019", "#ff0000", 4000],   # 真神光耀
                       "c36996": ["12452", "#00ffff", 3000],  # 真神光耀
                       "c37005": ["3398", "#ff7777", 3000],  # 恶毒利刃
                       "c37043": ["3447", "#ff7700", 5000],  # 初窥灵光
                       "c36999": ["12453", "#ff0077", 25000],  # 旋转火刀
                       "c37059": ["3398", "#0077ff", 3000],  # 恶毒利刃
                       }

        # 赤幽明数据格式：
        # P1, P2, 倒影, 群攻黑影, 单体黑影

        self.heiying = {}
        self.lastHuodaoStart = 0
        self.lastHuodao = 0
        self.lastHuodaoEnd = 0

        self.bh.critPeriodDesc = "从每次[旋转火刀]的[余焰震爆]之前5秒开始，到伤害出现时结束"

        for line in self.bld.info.player:
            self.statDict[line]["battle"] = {"P1DPS": 0,
                                             "P2DPS": 0,
                                             "daoyingDPS": 0,
                                             "heiyingDPS1": 0,
                                             "heiyingDPS2": 0,}


    def __init__(self, bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint, config):
        '''
        对类本身进行初始化。
        '''
        super().__init__(bld, occDetailList, startTime, finalTime, battleTime, bossNamePrint)
        self.config = config

