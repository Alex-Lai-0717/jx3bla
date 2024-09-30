# coding:utf-8
from flask import Flask, render_template, url_for, request, redirect, session, make_response, jsonify, abort
from flask import request    
from flask import make_response,Response
from flask_cors import CORS
import urllib
import json
import re
import pymysql
import random
import time
import gc
import urllib.request
import hashlib
import configparser
import os
import traceback
from Constants import *

from tools.Functions import *
from tools.Names import *
from equip.AttributeDisplay import AttributeDisplay
from tools.painter import XiangZhiPainter
from replayer.ReplayerBase import RankCalculator

version = EDITION
ip = "127.0.0.1" # IP
announcement = "全新的DPS统计已出炉，大家可以关注一下，看一下各门派的表现~"
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.ad = AttributeDisplay()

# 数据库的屎山
STAT_ID = {"score": 3, "rhps": 18, "hps": 20, "rdps": 22, "ndps": 24, "mrdps": 26, "mndps": 28}
RANK_ID = {"score": 17, "rhps": 19, "hps": 21, "rdps": 23, "ndps": 25, "mrdps": 27, "mndps": 29}

def Response_headers(content):
    resp = Response(content)    
    resp.headers['Access-Control-Allow-Origin'] = '*'    
    return resp
    
@app.route('/getAnnouncement', methods=['GET'])
def getAnnouncement():
    edition = request.args.get('edition')
    if parseEdition(edition) < 0:
        return jsonify({"available": 0})
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    sql = '''SELECT * FROM PreloadInfo;'''
    cursor.execute(sql)
    result = cursor.fetchall()
    dataDict = {}
    for line in result:
        dataDict[line[0]] = line[1]
    dataDict["url"] = dataDict["updateurl"]
    db.close()
    return jsonify(dataDict)

@app.route('/setAnnouncement', methods=['POST'])
def setAnnouncement():
    jdata = json.loads(request.form.get('jdata'))
    print(jdata)
    version = jdata["version"]
    announcement = jdata["announcement"]
    updateurl = jdata["updateurl"]
    dataDict = {"version": version,
                "announcement": announcement,
                "updateurl": updateurl}

    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    for key in dataDict:
        sql = '''DELETE FROM PreloadInfo WHERE datakey = "%s";''' % key
        cursor.execute(sql)
        sql = '''INSERT INTO PreloadInfo VALUES ("%s", "%s");''' % (key, dataDict[key])
        cursor.execute(sql)
    db.commit()
    db.close()
    
    return jsonify({'result': 'success'})

@app.route('/getAttribute', methods=['POST'])
def getAttribute():
    '''
    远程获取属性，通过传入配装来获取属性.
    由于要一次获取多个玩家的配装，这个方法之后会废弃.
    '''
    jdata = json.loads(request.form.get('jdata'))
    print(jdata)
    equipStr = jdata["equipStr"]
    occ = jdata["occ"]
    res = app.ad.Display(equipStr, occ)
    return jsonify(res)

@app.route('/getGroupAttribute', methods=['POST'])
def getGroupAttribute():
    '''
    远程获取全团属性，通过传入团队的配装信息来获取属性.
    这个传入的方式与上面的方法不同.
    之后要对这个方法进行扩展，从而支持装备的缓存或者远程读取，这样属性计算会更精确.
    '''

    jdata = json.loads(request.form.get('jdata'))
    requests = jdata
    results = {}
    ad = AttributeDisplay()
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    for playerEquip in requests["players"]:
        if playerEquip["equipStr"] != "":  # 有装备
            results[playerEquip["id"]] = {}
            results[playerEquip["id"]]["base"] = ad.GetBaseAttrib(playerEquip["equipStr"], playerEquip["occ"])
            results[playerEquip["id"]]["panel"] = ad.GetPanelAttrib(playerEquip["equipStr"], playerEquip["occ"])
            results[playerEquip["id"]]["status"] = "success"
            # 记录当前的装备
            sql = '''DELETE FROM EquipmentInfo WHERE id="%s" and server="%s" and occ="%s";''' % (
                playerEquip["name"], playerEquip.get("server", "unknown"), playerEquip["occ"])
            cursor.execute(sql)
            sql = '''INSERT INTO EquipmentInfo VALUES ("%s", "%s", "%s", "%s", "%s", "%s", %d);''' % (
                playerEquip["name"], playerEquip.get("server", "unknown"), playerEquip["id"], playerEquip["occ"], playerEquip["equipStr"], playerEquip["score"], int(time.time()))
            cursor.execute(sql)
        else:  # 没有装备信息
            # 尝试从数据库读取
            sql = '''SELECT equip, score FROM EquipmentInfo WHERE id = "%s" AND server = "%s" and occ = "%s";''' % (
                playerEquip["name"], playerEquip.get("server", "unknown"), playerEquip["occ"])
            cursor.execute(sql)
            result = cursor.fetchall()
            if result:
                results[playerEquip["id"]] = {}
                equipStr = result[0][0]
                results[playerEquip["id"]]["status"] = "cached"
                results[playerEquip["id"]]["equipStr"] = equipStr
                results[playerEquip["id"]]["score"] = result[0][1]
                results[playerEquip["id"]]["base"] = ad.GetBaseAttrib(equipStr, playerEquip["occ"])
                results[playerEquip["id"]]["panel"] = ad.GetPanelAttrib(equipStr, playerEquip["occ"])
            else:
                results[playerEquip["id"]] = {}
                results[playerEquip["id"]]["status"] = "notfound"

    db.commit()
    db.close()
    return jsonify(results)

@app.route('/getPercentInfo', methods=['GET'])
def getPercentInfo():
    '''
    获取百分位排名信息.
    '''
    res = app.percent_data
    gc.collect()
    return jsonify({'result': 'success', 'data': res})
    
@app.route('/refreshRateData', methods=['GET', 'POST'])
def refreshRateData():
    '''
    刷新服务器上的百分位排名数据.
    '''
    print("Updating rank data...")
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    sql = """SELECT * FROM ReplayProStatRank"""
    cursor.execute(sql)
    result = cursor.fetchall()

    db.close()
    
    percent_data = {}
    for line in result:
        percent_data[line[0]] = {"num": line[1], "value": line[2]}
    
    app.percent_data = percent_data
    
    print("Rank data updated!")
    return jsonify({'result': 'success'})
    
    
@app.route('/getUuid', methods=['POST'])
def getUuid():
    mac = request.form.get('mac')
    userip = request.remote_addr
    intTime = int(time.time())
    
    hashStr = mac + ip + str(intTime)
    uuid = hashlib.md5(hashStr.encode(encoding="utf-8")).hexdigest()
    
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    
    sql = '''INSERT INTO UserInfo VALUES ("%s", "%s", "%s", "%s", %d, %d, %d, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);'''%(uuid, "", mac, userip, intTime, 0, 0)
    cursor.execute(sql)
    
    db.commit()
    db.close()
    
    return jsonify({'uuid': uuid})
    
@app.route('/setUserId', methods=['POST'])
def setUserId():
    uuid = request.form.get('uuid')
    id = request.form.get('id')
    
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    
    sql = '''SELECT * from UserInfo WHERE uuid = "%s"'''%(uuid)
    cursor.execute(sql)
    result = cursor.fetchall()
    
    sql = '''SELECT * from UserInfo WHERE id = "%s"'''%(id)
    cursor.execute(sql)
    result2 = cursor.fetchall()
    
    if result:
    
        if result[0][1] != "":
            db.close()
            return jsonify({'result': 'hasuuid'})
        elif result2:
            db.close()
            return jsonify({'result': 'dupid'})
        else:
            sql = """UPDATE UserInfo SET id="%s" WHERE uuid="%s";"""%(id, uuid)
            cursor.execute(sql)
            db.commit()
            db.close()
            return jsonify({'result': 'success'})
    else:
        db.close()
        return jsonify({'result': 'nouuid'})
        

@app.route('/getUserInfo', methods=['POST'])
def getUserInfo():
    uuid = request.form.get('uuid')
    
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    sql = '''SELECT * from UserInfo WHERE uuid = "%s"'''%(uuid)
    cursor.execute(sql)
    result = cursor.fetchall()
    
    response = {'exist': 0}
    
    if result:
        response["exist"] = 1
        response["item1"] = result[0][7]
        response["item2"] = result[0][8]
        response["item3"] = result[0][9]
        response["item4"] = result[0][10]
        response["exp"] = result[0][6]
        response["score"] = result[0][5]
        response["lvl"] = result[0][17]
        
    db.close()
    return jsonify(response)
    
    
@app.route('/userLvlup', methods=['POST'])
def userLvlup():
    uuid = request.form.get('uuid')
    
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    sql = '''SELECT * from UserInfo WHERE uuid = "%s"'''%(uuid)
    cursor.execute(sql)
    result = cursor.fetchall()
    
    response = {'result': "fail"}
    
    if result:
        lvl = result[0][17]
        exp = result[0][6]
        if exp >= LVLTABLE[lvl+1]:
            response["result"] = "success"
            item = [0, 0, 0, 0]
                
            response["info"] = ""
            
            sql = """UPDATE UserInfo SET item1=%d, item2=%d, item3=%d, item4=%d, lvl=%d WHERE uuid="%s";"""%(item[0], item[1], item[2], item[3], lvl+1, uuid)
            cursor.execute(sql)
    
    db.commit()
    db.close()
    return jsonify(response)

def receiveBattle(jdata, cursor):
    '''
    接收battle的json信息并进行入库处理.
    params:
    - jdata: json格式的battle信息.
    - cursor: 数据库操作的指针.
    '''
    server = jdata["server"]
    boss = jdata["boss"]
    battleDate = jdata["battledate"]
    mapName = jdata["mapdetail"]
    edition = jdata["edition"]
    hash = jdata["hash"]
    statistics = str(jdata["statistics"]).replace('"', '`')
    map = getIDFromMap(mapName)
    gameEdition = getGameEditionFromTime(map, jdata["begintime"])

    response = {}

    if "win" not in jdata:
        jdata["win"] = 1

    win = int(jdata["win"])

    if "time" not in jdata:
        jdata["time"] = 0
    if "begintime" not in jdata:
        jdata["begintime"] = 0
    if "userid" not in jdata:
        jdata["userid"] = "unknown"

    submitTime = jdata["time"]
    battleTime = jdata["begintime"]
    userID = jdata["userid"]
    editionFull = parseEdition(edition)

    # 增加五个字段：editionfull INT, userid VARCHAR(32), battletime INT, submittime INT, instanceid VARCHAR(32)
    sql = '''SELECT * from ActorStat WHERE hash = "%s"''' % hash
    cursor.execute(sql)
    result = cursor.fetchall()

    scoreSuccess = 1
    scoreAdd = 0

    dupID = 0

    mapid = getIDFromMap(mapName)
    if mapid in MAP_DICT_RECORD_LOGS and MAP_DICT_RECORD_LOGS[mapid]:
        mapDetail = mapid
        scoreAdd = MAP_DICT_RECORD_LOGS[mapid]
    else:
        scoreSuccess = 0
        response['scoreStatus'] = 'illegal'
        mapDetail = '0'

    if win == 0:
        scoreSuccess = 0
        response['scoreStatus'] = 'notwin'

    if result and result[0][6] == 1:
        sql = '''SELECT * from ScoreInfo WHERE reason LIKE "%%%s%%"''' % (hash)
        cursor.execute(sql)
        result2 = cursor.fetchall()
        if result2:
            scoreSuccess = 0
            response['scoreStatus'] = 'dupid'
        else:
            lastTime = result[0][10]
            if submitTime - lastTime > 180:
                scoreSuccess = 0
                response['scoreStatus'] = 'expire'

        if parseEdition(result[0][4]) >= parseEdition(edition):
            dupID = 1
        else:
            print("Update edition")

    sql = '''SELECT * from UserInfo WHERE uuid = "%s"''' % (userID)
    cursor.execute(sql)
    result = cursor.fetchall()
    if not result or result[0][1] == "":
        scoreSuccess = 0
        response['scoreStatus'] = 'nologin'

    if scoreSuccess and scoreAdd > 0:
        sql = """UPDATE UserInfo SET score=%d, exp=%d WHERE uuid="%s";""" % (
        result[0][5] + scoreAdd, result[0][6] + scoreAdd, userID)
        cursor.execute(sql)

        sql = """INSERT INTO ScoreInfo VALUES ("", "%s", %d, "%s", %d)""" % (
            userID, int(time.time()), "提交战斗记录：%s" % hash, scoreAdd)
        cursor.execute(sql)

        response['scoreStatus'] = 'success'
        response['scoreAdd'] = scoreAdd

    if dupID:
        print("Find Duplicated")
        response['result'] = 'dupid'
        return response

    sql = '''DELETE FROM ActorStat WHERE hash = "%s"''' % hash
    cursor.execute(sql)

    with open("database/ActorStat/%s" % hash, "w") as f:
        f.write(str(statistics))

    sql = """INSERT INTO ActorStat VALUES ("%s", "%s", "%s", "%s", "%s", "%s", %d, %d, "%s", %d, %d, "", "%s")""" % (
        server, boss, battleDate, mapDetail, edition, hash, win, editionFull, userID, battleTime, submitTime, gameEdition)
    cursor.execute(sql)

    del statistics

    response['result'] = 'success'
    response['hash'] = hash
    return response


@app.route('/uploadActorData', methods=['POST'])
def uploadActorData():
    jdata = json.loads(request.form.get('jdata'))
    # print(jdata)

    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    res = receiveBattle(jdata, cursor)
    return jsonify(res)
    
def getRank(value, table):
    '''
    获取单个数值的百分位排名.
    '''
    l = 0
    r = 101
    while r > l + 1:
        m = (l + r + 1) // 2
        if value >= table[m]:
            l = m
        else:
            r = m
    percent = l
    return percent
    
def getRankFromKeys(value, occ, map, boss, name, key, gameEdition):
    '''
    按key的格式，从数据库中找到对应的百分比排名.
    '''
    percent_key = "%s-%s-%s-%s-%s-%s" % (occ, map, boss, name, key, gameEdition)
    if percent_key in app.percent_data:
        table = json.loads(app.percent_data[percent_key]["value"])
        rank = getRank(value, table)
        return rank
    else:
        return -1

def receiveReplay(jdata, cursor):
    '''
    接收replay的json信息并进行入库处理.
    params:
    - jdata: json格式的replay信息.
    - cursor: 数据库操作的指针.
    '''
    server = jdata["server"]
    id = jdata["id"]
    if "·" in id:
        server = id.split("·")[1]
        id = id.split("·")[0]
    score = jdata["score"]
    battleDate = jdata["battledate"]
    mapDetail = jdata["mapdetail"]
    boss = jdata["boss"]
    edition = jdata["edition"]
    hash = jdata["hash"]
    statistics = jdata["statistics"]
    public = jdata["public"]
    submitTime = jdata["submittime"]
    battleTime = jdata["battletime"]
    userID = jdata["userid"]
    editionFull = jdata["editionfull"]
    occ = jdata["occ"]
    replayedition = jdata["replayedition"]
    battleID = jdata.get("battleID", "")
    map = getIDFromMap(mapDetail)
    gameEdition = getGameEditionFromTime(map, battleTime)

    if editionFull <= parseEdition("8.1.1"):
        score *= 100

    sql = '''SELECT score from ReplayProStat WHERE mapdetail = "%s" and boss = "%s" and occ = "%s" and editionfull >= %d and gameEdition = "%s"''' % (mapDetail, boss, occ, parseEdition("8.3.5"), gameEdition)
    cursor.execute(sql)
    result = cursor.fetchall()
    num = 0
    numOver = 0
    for line in result:
        if line[0] == 0:
            continue
        num += 1
        if score > line[0]:
            numOver += 1
    numSameOcc = num

    # print(num, numOver)

    sql = '''SELECT shortID, public, editionfull, scoreRank from ReplayProStat WHERE hash = "%s"''' % hash
    cursor.execute(sql)
    result = cursor.fetchall()
    if result:
        if result[0][2] >= editionFull and (result[0][1] == 1 or public == 0):
            print("Find Duplicated")
            shortID = result[0][0]
            scoreRank = result[0][3]
            return {'result': 'dupid', 'num': num, 'numOver': numOver, 'shortID': shortID, 'scoreRank': scoreRank}
        else:
            print("Update edition")

    sql = '''DELETE FROM ReplayProStat WHERE hash = "%s"''' % hash
    cursor.execute(sql)

    # 更新数量
    sql = '''SELECT * from ReplayProInfo WHERE dataname = "num"'''
    cursor.execute(sql)
    result = cursor.fetchall()
    num = result[0][2]
    shortID = num + 1
    sql = """UPDATE ReplayProInfo SET datavalueint=%d WHERE dataname = "num";""" % shortID
    cursor.execute(sql)

    statistics["overall"]["shortID"] = shortID

    with open("database/ReplayProStat/%d" % shortID, "w") as f:
        f.write(str(statistics))

    scoreRank = getRankFromKeys(score, occ, map, boss, "stat", "score", gameEdition)
    rhps = statistics["skill"]["healer"].get("rhps", 0)
    rhpsRank = getRankFromKeys(score, occ, map, boss, "stat", "rhps", gameEdition)
    hps = statistics["skill"]["healer"].get("hps", 0)
    hpsRank = getRankFromKeys(score, occ, map, boss, "stat", "hps", gameEdition)
    rdps = statistics["skill"]["general"].get("rdps", 0)
    rdpsRank = getRankFromKeys(score, occ, map, boss, "stat", "rdps", gameEdition)
    ndps = statistics["skill"]["general"].get("ndps", 0)
    ndpsRank = getRankFromKeys(score, occ, map, boss, "stat", "ndps", gameEdition)
    mrdps = statistics["skill"]["general"].get("mrdps", 0)
    mrdpsRank = getRankFromKeys(score, occ, map, boss, "stat", "mrdps", gameEdition)
    mndps = statistics["skill"]["general"].get("mndps", 0)
    mndpsRank = getRankFromKeys(score, occ, map, boss, "stat", "mndps", gameEdition)
    hold = 1

    del statistics

    print("[UpdateReplay]", server, id, occ, score, battleDate, mapDetail, boss, hash, shortID, public, edition, editionFull, replayedition, userID, battleTime,
        submitTime, battleID, scoreRank, rhps, rhpsRank, hps, hpsRank, rdps, rdpsRank, ndps, ndpsRank, mrdps, mrdpsRank, mndps, mndpsRank, hold)

    sql = """INSERT INTO ReplayProStat VALUES ("%s", "%s", "%s", %.2f, "%s", "%s", "%s", "%s", %d, %d, "%s", %d, "%s", "%s", %d, %d, "%s",
%d, %.2f, %d, %.2f, %d, %.2f, %d, %.2f, %d, %.2f, %d, %.2f, %d, %d, "%s")""" % (
        server, id, occ, score, battleDate, mapDetail, boss, hash, shortID, public, edition, editionFull, replayedition, userID, battleTime,
        submitTime, battleID, scoreRank, rhps, rhpsRank, hps, hpsRank, rdps, rdpsRank, ndps, ndpsRank, mrdps, mrdpsRank, mndps, mndpsRank, hold, gameEdition)
    cursor.execute(sql)

    return {'result': 'success', 'num': numSameOcc, 'numOver': numOver, 'shortID': shortID, 'scoreRank': scoreRank}

@app.route('/uploadReplayPro', methods=['POST'])
def uploadReplayPro():
    jdata = json.loads(request.form.get('jdata'))
    print("Starting uploadReplay...")
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    try:
        res = receiveReplay(jdata, cursor, "-1")
        db.commit()
        db.close()
    except Exception as e:
        traceback.print_exc()
        db.close()
        return jsonify({'result': 'fail', 'num': 0, 'numOver': 0, 'shortID': 0, 'scoreRank': 0})
    print("UploadReplay complete!")
    return jsonify(res)

@app.route('/uploadCombinedData', methods=['POST'])
def uploadCombinedData():
    jdata = json.loads(request.form.get('jdata'))
    groupRes = {"data": [], "status": "success"}

    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    # battleID = "0"
    try:
        for line in jdata["data"]:
            if line["type"] == "replay":
                # 单个复盘
                res = receiveReplay(line["data"], cursor)
                res["id"] = line["id"]
                groupRes["data"].append(res)
            elif line["type"] == "battle":
                # 整场战斗的数据
                res = receiveBattle(line["data"], cursor)
                res["id"] = line["id"]
                groupRes["data"].append(res)
        db.commit()
        db.close()
    except Exception as e:
        traceback.print_exc()
        db.close()
        groupRes["status"] = "fail"
    return jsonify(groupRes)


@app.route('/showReplayPro.html', methods=['GET'])
def showReplayPro():
    id = request.args.get('id')
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    sql = """SELECT shortID, public, replayedition, occ FROM ReplayProStat WHERE shortID = %s OR hash = "%s";"""%(id, id)
    cursor.execute(sql)
    result = cursor.fetchall()
    db.close()
    if len(result) == 0:
        text = "结果未找到."
    elif result[0][1] == 0:
        text = "数据未公开."
    elif result[0][3] != "unknown": #in ["xiangzhi", "lingsu", "lijingyidao", "butianjue", "yunchangxinjing"]:
        # 生成复盘页面
        occ = result[0][3]
        with open("database/ReplayProStat/%d" % result[0][0], "r") as f:
            text = f.read().replace('\n', '\\n').replace('\t', '\\t')
        # text = result[0][0].decode().replace('\n', '\\n').replace('\t', '\\t')
        text1 = text.replace("'", '"')
        jResult = json.loads(text1)
        rc = RankCalculator(jResult, app.percent_data)
        rank = rc.getRankFromStat(occ)
        rankStr = json.dumps(rank)
        return render_template("HealerReplay.html", raw=text, rank=rankStr, occ=occ, edition=EDITION)
    return jsonify({'text': text.decode()})

@app.route('/getReplayPro', methods=['GET'])
def getReplayPro():
    id = request.args.get('id')
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    sql = """SELECT shortID, public, replayedition, occ, battleID, gameEdition FROM ReplayProStat WHERE shortID = %s OR hash = "%s";"""%(id, id)
    cursor.execute(sql)
    result = cursor.fetchall()
    flag = 0
    if len(result) == 0:
        flag = 0
        text = "结果未找到."
    elif result[0][1] == 0:
        flag = 0
        text = "数据未公开."
    elif result[0][3] != "unknown":  # in ["xiangzhi", "lingsu", "lijingyidao", "butianjue", "yunchangxinjing"]:
        flag = 1
        occ = result[0][3]
        with open("database/ReplayProStat/%d" % result[0][0], "r") as f:
            text = f.read().replace('\n', '\\n').replace('\t', '\\t').replace("'", '"')
        text1 = text
        jResult = json.loads(text1)
        rc = RankCalculator(jResult, app.percent_data, result[0][5])
        rank = rc.getRankFromStat(occ)
        rankStr = json.dumps(rank)
        battleID = result[0][4]
        gameEdition = result[0][5]
        teammateInfo = {}
        if battleID != "" and battleID != "NULL":
            # 找出同场战斗的编号
            sql = """SELECT id, shortID FROM ReplayProStat WHERE battleID = "%s";""" % battleID
            cursor.execute(sql)
            result2 = cursor.fetchall()
            for line in result2:
                teammateInfo[line[0]] = line[1]
        print('[TeammateInfo]', teammateInfo)
    else:
        flag = 0
        text = "不支持的心法，请等待之后的版本更新."
    db.close()
    if flag:
        return jsonify({'available': 1, 'text': "请求成功", 'raw': text1, 'rank': rankStr, 'teammate': str(teammateInfo), 'battleID': battleID, 'gameEdition': gameEdition})
    else:
        return jsonify({'available': 0, 'text': text})

@app.route('/getBattle', methods=['GET'])
def getBattle():
    hash = request.args.get('hash')
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    sql = """SELECT server, boss, battleDate, mapDetail, edition, battleTime, submitTime, gameEdition FROM ActorStat WHERE hash = "%s";"""%(hash)
    cursor.execute(sql)
    result = cursor.fetchall()
    flag = 0
    if len(result) == 0:
        flag = 0
        text = "结果未找到."
    else:
        flag = 1
        with open("database/ActorStat/%s" % hash, "r") as f:
            text = f.read().replace('\n', '\\n').replace('\t', '\\t').replace("'", '"')
        text1 = text
        jResult = json.loads(text1)
        act = {"available": 0}
        if "act" in jResult:
            act["available"] = 1
            act = jResult["act"]
    db.close()
    if flag:
        return jsonify({'available': 1, 'text': "请求成功", "act": act, "server": result[0][0], "boss": result[0][1],
                        "battleDate": result[0][2], "mapDetail": result[0][3], "edition": result[0][4],
                        "battleTime": result[0][5], "submitTime": result[0][6], "gameEdition": result[0][7]})
    else:
        return jsonify({'available': 0, 'text': text})


@app.route('/getMultiPlayer', methods=['GET'])
def getMultiPlayer():
    server = request.args.get('server')
    ids = request.args.get('ids')
    map = request.args.get('map')

    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()
    ids_split = ids.split(' ')

    overallResJson = {}
    overallResJson["server"] = server
    for id in ids_split:
        sql = '''SELECT * FROM ReplayProStat WHERE server = "%s" AND id = "%s" AND mapdetail = "%s" AND public = 1''' % (server, id, map)
        cursor.execute(sql)
        result = cursor.fetchall()
        resJson = {"stat": {}}
        highestScore = {}
        sumScore = {}
        numRecord = {}
        avgScore = {}

        rankStat = {}
        for stat_item in RANK_ID:
            rankStat[stat_item] = {"overallSum": 0, "overallAverage": 0}

        allResults = {}
        for record in result:
            score = record[3]
            boss = record[6]
            occ = record[2]
            edition = record[11]
            battleTime = record[15]
            submitTime = record[16]
            shortID = record[8]
            if score > highestScore.get(boss, -1):
                highestScore[boss] = score
            numRecord[boss] = numRecord.get(boss, 0) + 1
            sumScore[boss] = sumScore.get(boss, 0) + score
            if boss not in allResults:
                allResults[boss] = []
            res = {"score": score, "occ": occ, "edition": edition, "battleTime": battleTime, "submitTime": submitTime,
                   "shortID": shortID}
            for stat_item in STAT_ID:
                res[stat_item] = record[STAT_ID[stat_item]]
            for stat_item in RANK_ID:
                rank = record[RANK_ID[stat_item]]
                res[stat_item + "Rank"] = rank
                if boss not in rankStat[stat_item]:
                    rankStat[stat_item][boss] = {"num": 0, "sum": 0, "highest": 0}
                if rank is not None:
                    rankStat[stat_item][boss]["num"] += 1
                    rankStat[stat_item][boss]["sum"] += rank
                    rankStat[stat_item][boss]["highest"] = max(rankStat[stat_item][boss]["highest"], rank)
            allResults[boss].append(res)
        numBoss = 0
        sumHighestScore = 0
        sumAverageScore = 0
        for boss in sumScore:
            numBoss += 1
            avgScore[boss] = roundCent(safe_divide(sumScore[boss], numRecord[boss]))
            sumHighestScore += highestScore[boss]
            sumAverageScore += avgScore[boss]
            resJson["stat"][boss] = {"highest": highestScore[boss], "average": avgScore[boss], "num": numRecord[boss]}
            for stat_item in RANK_ID:
                rankStat[stat_item][boss]["average"] = safe_divide(rankStat[stat_item][boss]["sum"], rankStat[stat_item][boss]["num"])
                rankStat[stat_item]["overallSum"] += rankStat[stat_item][boss]["average"]

        overallAverageScore = roundCent(safe_divide(sumAverageScore, numBoss))
        overallHighestScore = roundCent(safe_divide(sumHighestScore, numBoss))
        for stat_item in RANK_ID:
            rankStat[stat_item]["overallAverage"] += roundCent(safe_divide(rankStat[stat_item]["overallSum"], numBoss))

        resJson["stat"]["overall"] = {"highest": overallHighestScore, "average": overallAverageScore, "num": numBoss}
        resJson["rank"] = rankStat
        resJson["table"] = allResults

        overallResJson[id] = resJson
    db.close()
    return jsonify({'available': 1, 'text': "请求成功", 'result': overallResJson})

@app.route('/getSinglePlayer', methods=['GET'])
def getSinglePlayer():
    server = request.args.get('server')
    id = request.args.get('id')
    map = request.args.get('map')
    occ = request.args.get('occ')  # 如果以后要加限定心法, 就用这个参数；现在暂时用不上
    gameEdition = request.args.get('gameEdition')

    if occ is None:
        occ = "all"
    if gameEdition is None:
        gameEdition = "all"

    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    sql = '''SELECT * FROM ReplayProStat WHERE server = "%s" AND id = "%s" AND mapdetail = "%s" AND public = 1 AND gameEdition = "%s"''' % (server, id, map, gameEdition)
    if gameEdition == "all":
        sql = '''SELECT * FROM ReplayProStat WHERE server = "%s" AND id = "%s" AND mapdetail = "%s" AND public = 1''' % (server, id, map)
    cursor.execute(sql)
    result = cursor.fetchall()
    resJson = {"stat": {}}
    highestScore = {}
    sumScore = {}
    numRecord = {}
    avgScore = {}

    rankStat = {}
    for stat_item in RANK_ID:
        rankStat[stat_item] = {"overallSum": 0, "overallAverage": 0, "overallMaxSum": 0, "overallMaxAverage": 0}

    allResults = {}
    for record in result:
        score = record[3]
        boss = record[6]
        occ = record[2]
        edition = record[10]
        battleTime = record[14]
        submitTime = record[15]
        battleID = record[16]
        shortID = record[8]
        if score > highestScore.get(boss, -1):
            highestScore[boss] = score
        numRecord[boss] = numRecord.get(boss, 0) + 1
        sumScore[boss] = sumScore.get(boss, 0) + score
        if boss not in allResults:
            allResults[boss] = []
        res = {"score": score, "occ": occ, "edition": edition, "battleTime": battleTime, "submitTime": submitTime, "shortID": shortID, "battleID": battleID}
        for stat_item in STAT_ID:
            res[stat_item] = record[STAT_ID[stat_item]]
        for stat_item in RANK_ID:
            rank = record[RANK_ID[stat_item]]
            res[stat_item + "Rank"] = rank
            if boss not in rankStat[stat_item]:
                rankStat[stat_item][boss] = {"num": 0, "sum": 0, "highest": 0}
            if rank is not None:
                rankStat[stat_item][boss]["num"] += 1
                rankStat[stat_item][boss]["sum"] += rank
                rankStat[stat_item][boss]["highest"] = max(rankStat[stat_item][boss]["highest"], rank)
        allResults[boss].append(res)
    numBoss = 0
    sumHighestScore = 0
    sumAverageScore = 0
    for boss in sumScore:
        numBoss += 1
        avgScore[boss] = roundCent(safe_divide(sumScore[boss], numRecord[boss]))
        sumHighestScore += highestScore.get(boss, 0)
        sumAverageScore += avgScore.get(boss, 0)
        resJson["stat"][boss] = {"highest": highestScore.get(boss, 0), "average": avgScore.get(boss, 0), "num": numRecord.get(boss, 0)}
        for stat_item in RANK_ID:
            rankStat[stat_item][boss]["average"] = safe_divide(rankStat[stat_item][boss]["sum"], rankStat[stat_item][boss]["num"])
            rankStat[stat_item]["overallSum"] += rankStat[stat_item][boss]["average"]
            rankStat[stat_item]["overallMaxSum"] += rankStat[stat_item][boss]["highest"]

    overallAverageScore = roundCent(safe_divide(sumAverageScore, numBoss))
    overallHighestScore = roundCent(safe_divide(sumHighestScore, numBoss))
    for stat_item in RANK_ID:
        rankStat[stat_item]["overallAverage"] += roundCent(safe_divide(rankStat[stat_item]["overallSum"], numBoss))
        rankStat[stat_item]["overallMaxAverage"] += roundCent(safe_divide(rankStat[stat_item]["overallMaxSum"], numBoss))

    resJson["stat"]["overall"] = {"highest": overallHighestScore, "average": overallAverageScore, "num": numBoss}
    resJson["rank"] = rankStat
    resJson["table"] = allResults

    db.close()
    return jsonify({'available': 1, 'text': "请求成功", 'result': resJson})

@app.route('/getXinfaRank', methods=['GET'])
def getXinfaRankfunc():
    map = request.args.get('map')
    boss = request.args.get("boss")
    orderby = request.args.get("orderby")
    if orderby not in ["score", "rhps", "hps", "rdps", "ndps", "mrdps", "mndps"]:
        return jsonify({'available': 0, 'text': "排序方式不合法"})
    mapid = getIDFromMap(map)
    gameEdition = request.args.get("gameEdition")
    result = {}
    case = "general"
    if orderby in ["rhps", "hps"]:
        case = "healer"
    if gameEdition is None:
        gameEdition = "all"

    occ_collect = []

    for key in OCC_PINYIN_DICT:
        occ_pinyin = OCC_PINYIN_DICT[key]
        if occ_pinyin == "unknown":
            continue
        if mapid == "未知":
            continue
        tablekey = "%s-%s-%s-%s-%s-%s" % (occ_pinyin, mapid, boss, case, orderby, gameEdition)
        if tablekey in app.percent_data:
            #result[occ_pinyin] = app.percent_data[tablekey]
            table = json.loads(app.percent_data[tablekey]["value"])
            # occ_collect.append([occ_pinyin, table[75]])
            occ_collect.append({"name": occ_pinyin, "num": app.percent_data[tablekey]["num"], "value": table})

    occ_collect.sort(key=lambda x:-x["value"][75])

    # real_result = []
    # for line in occ_collect:
    #     real_result.append({"name": line[0], "value": result[line[0]]["value"], "num": result[line[0]]["num"]})

    return jsonify({'available': 1, 'text': "请求成功", 'result': occ_collect})



@app.route('/getRank', methods=['GET'])
def getRankfunc():
    map = request.args.get('map')
    boss = request.args.get("boss")
    occ = request.args.get("occ")
    page = request.args.get("page")
    orderby = request.args.get("orderby")
    alltime = request.args.get("alltime")
    gameEdition = request.args.get("gameEdition")
    if page is None:
        page = 1
    else:
        page = int(page)
    if orderby is None:
        orderby = "score"
    if alltime is None:
        alltime = 1
    if orderby not in ["score", "rhps", "hps", "rdps", "ndps", "mrdps", "mndps", "battletime"]:
        return jsonify({'available': 0, 'text': "排序方式不合法"})
    if gameEdition is None:
        gameEdition = "all"

    if orderby == "battletime":
        order_id = 4
    else:
        if alltime:
            order_id = STAT_ID[orderby]
        else:
            order_id = RANK_ID[orderby]

    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    numPerPage = 50

#     sql = '''SELECT server, id, score, edition, battletime, submittime, shortID, scoreRank, rhps, rhpsRank,
# hps, hpsRank, rdps, rdpsRank, ndps, ndpsRank, mrdps, mrdpsRank, mndps, mndpsRank
# FROM ReplayProStat WHERE mapdetail = "%s" AND boss = "%s" AND occ = "%s" AND public = 1''' % (map, boss, occ)

    sql = '''SELECT * FROM ReplayProStat WHERE mapdetail = "%s" AND boss = "%s" AND occ = "%s" AND public = 1 AND gameEdition = "%s"''' % (map, boss, occ, gameEdition)
    if gameEdition == "all":
        sql = '''SELECT * FROM ReplayProStat WHERE mapdetail = "%s" AND boss = "%s" AND occ = "%s" AND public = 1''' % (map, boss, occ)
    cursor.execute(sql)
    result = cursor.fetchall()
    resJson = {"table": []}

    result = list(result)
    result_var = []
    for line in result:
        line_var = list(line)
        if parseEdition(line[10]) < parseEdition("8.1.0") and occ in ["lingsu", "butianjue", "yunchangxinjing"]:
            line_var[3] -= 10000
        if line_var[order_id] is None:
            continue
        line_var.append(line_var[order_id])
        skip = 0
        if parseEdition(line[10]) < parseEdition("8.4.0") and getIDFromMap(line[5]) == "588" and line[6] == "李重茂":
            skip = 1
        if parseEdition(line[10]) < parseEdition("8.5.0") and getIDFromMap(line[5]) == "588" and line[6] == "李重茂" and line[0] in ["傲血戰意", "共結來緣"]:
            skip = 1
        if parseEdition(line[10]) < parseEdition("8.5.0") and orderby in ["rdps", "mrdps", "ndps", "mndps"] and line_var[STAT_ID[orderby]] == 0 and \
                occ in ["taixuanjing", "wenshuijue", "xiaochenjue", "beiaojue", "linghaijue", "yinlongjue", "gufengjue"]:
            skip = 1
        if not skip:
            result_var.append(line_var)
    result_var.sort(key=lambda x:-x[-1])

    result_nodup = []
    id_dict = {}
    for line in result_var:
        uid = "%s-%s-%s" % (line[0], line[1], line[31])
        if uid not in id_dict:
            id_dict[uid] = 1
            result_nodup.append(line)

    for i in range((page-1)*numPerPage, page*numPerPage):
        if i < len(result_nodup):
            record = result_nodup[i]
            if parseEdition(record[10]) < parseEdition("8.1.0") and occ in ["lingsu", "butianjue", "yunchangxinjing"]:
                record[3] += 10000
            server = record[0]
            id = record[1]
            score = record[3]
            edition = record[10]
            battleTime = record[14]
            submitTime = record[15]
            shortID = record[8]
            res = {"score": score, "server": server, "edition": edition, "id": id, "battleTime": battleTime, "submitTime": submitTime, "shortID": shortID}
            for id in STAT_ID:
                res[id] = record[STAT_ID[id]]
            for id in RANK_ID:
                res[id+"Rank"] = record[RANK_ID[id]]
            res["hold"] = record[30]
            res["battleID"] = record[16]
            resJson["table"].append(res)

    resJson["num"] = len(result_nodup)
    db.close()

    return jsonify({'available': 1, 'text': "请求成功", 'result': resJson})
    
# @app.route('/uploadXiangZhiData', methods=['POST'])
# def uploadXiangZhiData():
#     jdata = json.loads(request.form.get('jdata'))
#     print(jdata)
#     server = jdata["server"]
#     id = jdata["id"]
#     score = jdata["score"]
#     battleDate = jdata["battledate"]
#     mapDetail = jdata["mapdetail"]
#     edition = jdata["edition"]
#     hash = jdata["hash"]
#     statistics = jdata["statistics"]
#
#     if "public" not in jdata:
#         jdata["public"] = 0
#
#     public = jdata["public"]
#
#     if "time" not in jdata:
#         jdata["time"] = 0
#     if "begintime" not in jdata:
#         jdata["begintime"] = 0
#     if "userid" not in jdata:
#         jdata["userid"] = "unknown"
#
#     submitTime = jdata["time"]
#     battleTime = jdata["begintime"]
#     userID = jdata["userid"]
#     editionFull = parseEdition(edition)
#
#     #增加五个字段：editionfull INT, userid VARCHAR(32), battletime INT, submittime INT, instanceid VARCHAR(32)
#
#     db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
#     cursor = db.cursor()
#
#     sql = '''SELECT score from XiangZhiStat WHERE mapdetail = "%s"'''%mapDetail
#     cursor.execute(sql)
#     result = cursor.fetchall()
#
#     num = 0
#     numOver = 0
#     for line in result:
#         if line[0] == 0:
#             continue
#         num += 1
#         if score > line[0]:
#             numOver += 1
#
#     print(num, numOver)
#
#     sql = '''SELECT * from XiangZhiStat WHERE hash = "%s"'''%hash
#     cursor.execute(sql)
#     result = cursor.fetchall()
#
#     if result:
#         if parseEdition(result[0][5]) >= parseEdition(edition):
#             print("Find Duplicated")
#             db.close()
#             return jsonify({'result': 'dupid', 'num': num, 'numOver': numOver})
#         else:
#             print("Update edition")
#
#     sql = '''DELETE FROM XiangZhiStat WHERE hash = "%s"'''%hash
#     cursor.execute(sql)
#
#     sql = """INSERT INTO XiangZhiStat VALUES ("%s", "%s", %d, "%s", "%s", "%s", "%s", "%s", %d, %d, "%s", %d, %d, "")"""%(
#         server, id, score, battleDate, mapDetail, edition, hash, statistics, public, editionFull, userID, battleTime, submitTime)
#     cursor.execute(sql)
#     db.commit()
#     db.close()
#
#     return jsonify({'result': 'success', 'num': num, 'numOver': numOver})
    
def initializePercent():
    '''
    初始化服务器上的排名信息.
    '''
    print("Initializing rank data...")
    db = pymysql.connect(host=ip, user=app.dbname, password=app.dbpwd, database="jx3bla", port=3306, charset='utf8')
    cursor = db.cursor()

    sql = """SELECT * FROM ReplayProStatRank"""
    cursor.execute(sql)
    result = cursor.fetchall()

    db.close()
    
    percent_data = {}
    for line in result:
        percent_data[line[0]] = {"num": line[1], "value": line[2]}
    
    app.percent_data = percent_data
    
    print("Rank data initialized!")
    
    
if __name__ == '__main__':
    import signal
    
    config = configparser.RawConfigParser()
    config.readfp(open('./settings.cfg'))
    
    app.dbname = config.get('jx3bla', 'username')
    app.dbpwd = config.get('jx3bla', 'password')
    app.debug = config.getboolean('jx3bla', 'debug')
    
    initializePercent()
    
    app.run(host='0.0.0.0',port=8009,debug=app.debug,threaded=True)

