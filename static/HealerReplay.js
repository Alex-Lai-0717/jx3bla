

function parseCent(x) {
    return (parseInt(x * 10000) / 100) + '%'
}

function parseDigit(x) {
    return (parseInt(x * 100) / 100);
}

function parseTime(time){
    time = parseInt(time)
    if (time < 60)
        return time + "s";
    else {
        if (time % 60 == 0)
            return parseInt(time / 60) + "m";
        else
            return parseInt(time / 60) + "m" + time % 60 + "s";
    }
}

function getLvl(score) {
    rateScale = [[100, "#dddd00", "A+", "不畏浮云遮望眼，只缘身在最高层。"],
                  [95, "#ff7777", "A", "独有凤凰池上客，阳春一曲和皆难。"],
                  [90, "#ff7777", "A-", "欲把一麾江海去，乐游原上望昭陵。"],
                  [85, "#ff7700", "B+", "敢将十指夸针巧，不把双眉斗画长。"],
                  [80, "#ff7700", "B", "云想衣裳花想容，春风拂槛露华浓。"],
                  [77, "#ff7700", "B-", "疏影横斜水清浅，暗香浮动月黄昏。"],
                  [73, "#0077ff", "C+", "青山隐隐水迢迢，秋尽江南草未凋。"],
                  [70, "#0077ff", "C", "花径不曾缘客扫，蓬门今始为君开。"],
                  [67, "#0077ff", "C-", "上穷碧落下黄泉，两处茫茫皆不见。"],
                  [63, "#77ff00", "D+", "人世几回伤往事，山形依旧枕寒流。"],
                  [60, "#77ff00", "D", "总为浮云能蔽日，长安不见使人愁。"],
                  [0, "#ff0000", "F", "仰天大笑出门去，我辈岂是蓬蒿人。"]]
    for (i in rateScale){
        if (score >= rateScale[i][0]) {
            return [rateScale[i][2], rateScale[i][1], rateScale[i][3]];
        }
    }
}

function getSkillPercent(name, key) {
    var color = "#000000";
    if (name in rankObj && key in rankObj[name]){
        //查找成功
        var num = rankObj[name][key]["num"];
        var percent = rankObj[name][key]["percent"];
        if (percent >= 95) {
            color = "#ff7700"
        } else if (percent >= 75) {
            color = "#330077"
        } else if (percent >= 50) {
            color = "#0000ff"
        } else if (percent >= 25) {
            color = "#007700"
        } else {
            color = "#aaaaaa"
        }
        return [num, percent, color];
    } else {
        //查找失败
        return [0, 0, "#000000"];
    }
}

repl = raw.replace(/'/g, '"').replace(/&#39;/g, '"').replace(/\n/g, '\\n').replace(/\t/g, '\\t');
resObj = JSON.parse(repl)

repl2 = rank.replace(/'/g, '"').replace(/&#34;/g, '"').replace(/\n/g, '\\n').replace(/\t/g, '\\t');
rankObj = JSON.parse(repl2)

// part 1
$('#data-1-1').html(resObj.overall.edition);
$('#data-1-2').html(resObj.overall.playerID);
$('#data-1-3').html(resObj.overall.server);
$('#data-1-4').html(resObj.overall.battleTimePrint);
$('#data-1-5').html(resObj.overall.generateTimePrint);
$('#data-1-6').html(resObj.overall.map);
$('#data-1-7').html(resObj.overall.boss);
$('#data-1-8').html(resObj.overall.numPlayer);
$('#data-1-9').html(resObj.overall.sumTimePrint);
$('#data-1-10').html(resObj.overall.dataType);

// part 2
if (resObj.equip.available) {
    $('#data-2-1').html(resObj.equip.score);
    $('#data-2-2').html(resObj.equip.sketch);
    $('#data-2-3').html(resObj.equip.forge);
    $('#data-2-4').html(resObj.equip.spirit);
    $('#data-2-5').html(resObj.equip.heal+"("+resObj.equip.healBase+")");
    $('#data-2-6').html(resObj.equip.critPercent+"("+resObj.equip.crit+")");
    $('#data-2-7').html(resObj.equip.critpowPercent+"("+resObj.equip.critpow+")");
    $('#data-2-8').html(resObj.equip.hastePercent+"("+resObj.equip.haste+")");
}
else {
    $('#data-2-t').addClass("hidden");
    $('#data-2-h').removeClass("hidden");
}

//part 3
var table=$("#data-3-t");
for (var i in resObj.healer.table){
    var tr = $("<tr></tr>");
    tr.appendTo(table);
    var td = $("<td>"+resObj.healer.table[i].name+"</td>");
    td.addClass("occ-"+resObj.healer.table[i].occ)
    td.appendTo(tr);

    var flag = false;
    if (resObj.healer.table[i].name == resObj["overall"]["playerID"]) {
        flag = true;
    }

    var td = $("<td>"+resObj.healer.table[i].healEff+"</td>");
    if (flag) {
        spRes = getSkillPercent("healer", "healEff");
        td.css("color", spRes[2]);
        td.addClass("stat-rank");
        td.attr("percent", spRes[1]);
        td.attr("num", spRes[0]);
    }
    td.appendTo(tr);
    var td = $("<td>"+resObj.healer.table[i].heal+"</td>");
    if (flag) {
        spRes = getSkillPercent("healer", "heal");
        td.css("color", spRes[2]);
        td.addClass("stat-rank");
        td.attr("percent", spRes[1]);
        td.attr("num", spRes[0]);
    }
    td.appendTo(tr);
}

//part 4
if (resObj.qixue.available) {
    result4 = "";
    for (var i = 1; i <= 12; i++) {
        result4 += resObj.qixue[i];
        if (i != 12) {
            result4 += ",";
        }
        if (i == 6) {
            result4 += "<br>";
        }
    }
    $('#data-4-t').html(result4);
}
else {
    $('#data-4-t').addClass("hidden");
    $('#data-4-h').removeClass("hidden");
}

//part 5

var SingleSkillDisplayer = function(skill, rank){
    this.log = [];
    this.skill = skill;
    this.rank = rank;
    this.setImage = function(id, name){
        this.id = id;
        this.name = name;
    }

    this.setSingle = function(style, desc, name, key){
        var value = this.skill[name][key];
        if (value == undefined) {
            value = 0;
        }
        this.log.push([style, desc, value, name, key]);
    }

    this.setDouble = function(style, desc, name, key1, key2){
        var value1 = this.skill[name][key1];
        if (value1 == undefined) {
            value1 = 0;
        }
        var value2 = this.skill[name][key2];
        if (value2 == undefined) {
            value2 = 0;
        }
        this.log.push([style, desc, value1, name, key1, value2, name, key2]);
    }

    this.export = function(frame, id, type){
        // 生成div
        var subarea = $("<div></div>");
        subarea.addClass("skill-subarea");
        subarea.appendTo(frame);
        if (type == "image") {
            var skillLeft = $("<div></div>");
            skillLeft.addClass("skill-left");
            var img = $('<img src="../static/icons/' + this.id + '.png">');
            img.appendTo(skillLeft);
            skillLeft.appendTo(subarea);
        }
        var skillRight = $("<div></div>");
        skillRight.addClass("skill-right");
        skillRight.appendTo(subarea);
        var table = $("<table></table>");
        table.appendTo(skillRight);
        var num = 0;
        for (i in this.log) {
            var line = this.log[i];
            var tr = $("<tr></tr>");
            tr.appendTo(table);
            // 第一列
            var td = $("<td></td>");
            td.html(line[1] + ":");
            td.appendTo(tr);
            // 第二列
            var td = $("<td></td>");
            if (line[0] == "int") {
                td.html(line[2]);
                spRes = getSkillPercent(line[3], line[4]);
            } else if (line[0] == "percent") {
                td.html(parseCent(line[2]));
                spRes = getSkillPercent(line[3], line[4]);
            } else if (line[0] == "delay") {
                td.html(line[2] + "ms");
                spRes = getSkillPercent(line[3], line[4]);
            } else if (line[0] == "plus") {
                td.html(line[2] + "+" + line[5]);
                spRes = getSkillPercent(line[3], line[4]);
            } else if (line[0] == "rate") {
                td.html(line[2] + "(" + parseDigit(line[5]) + ")");
                spRes = getSkillPercent(line[6], line[7]);
            }

            td.css("color", spRes[2]);
            if (spRes[0] > 0) {
                // 成功
                td.addClass("stat-rank");
                td.attr("percent", spRes[1]);
                td.attr("num", spRes[0]);
            } else {
                // 失败
            }
            td.appendTo(tr);
            num++;
        }
        if (num < 5) {
            table.css("margin-top", (5-num)*10 + "px");
        }
    }
}

var skillPanel = $('#skill');

if (occ == "xiangzhi") {
    mhsnDisplayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    mhsnDisplayer.setImage("7059", "梅花三弄")
    mhsnDisplayer.setDouble("rate", "数量", "meihua", "num", "numPerSec")
    mhsnDisplayer.setSingle("percent", "覆盖率", "meihua", "cover")
    mhsnDisplayer.setSingle("delay", "延迟", "meihua", "delay")
    mhsnDisplayer.setSingle("int", "犹香HPS", "meihua", "youxiangHPS")
    mhsnDisplayer.setSingle("int", "平吟HPS", "meihua", "pingyinHPS")
    mhsnDisplayer.export(skillPanel, 0, "image");

    zhiDisplayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    zhiDisplayer.setImage("7174", "徵")
    zhiDisplayer.setDouble("rate", "数量", "zhi", "num", "numPerSec")
    zhiDisplayer.setSingle("delay", "延迟", "zhi", "delay")
    zhiDisplayer.setSingle("int", "HPS", "zhi", "HPS")
    zhiDisplayer.setSingle("int", "古道HPS", "zhi", "gudaoHPS")
    zhiDisplayer.setSingle("percent", "有效比例", "zhi", "effRate")
    zhiDisplayer.export(skillPanel, 1, "image");

    jueDisplayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    jueDisplayer.setImage("7176", "角")
    jueDisplayer.setDouble("rate", "数量", "jue", "num", "numPerSec")
    jueDisplayer.setSingle("delay", "延迟", "jue", "delay")
    jueDisplayer.setSingle("int", "HPS", "jue", "HPS")
    jueDisplayer.setSingle("percent", "覆盖率", "jue", "cover")
    jueDisplayer.export(skillPanel, 2, "image");

    shangDisplayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    shangDisplayer.setImage("7172", "商")
    shangDisplayer.setDouble("rate", "数量", "shang", "num", "numPerSec")
    shangDisplayer.setSingle("delay", "延迟", "shang", "delay")
    shangDisplayer.setSingle("int", "HPS", "shang", "HPS")
    shangDisplayer.setSingle("percent", "覆盖率", "shang", "cover")
    shangDisplayer.export(skillPanel, 3, "image");

    gongDisplayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    gongDisplayer.setImage("7173", "宫")
    gongDisplayer.setDouble("rate", "数量", "gong", "num", "numPerSec")
    gongDisplayer.setSingle("delay", "延迟", "gong", "delay")
    gongDisplayer.setSingle("int", "HPS", "gong", "HPS")
    gongDisplayer.setSingle("int", "枕流HPS", "gong", "zhenliuHPS")
    gongDisplayer.setSingle("percent", "有效比例", "gong", "effRate")
    gongDisplayer.export(skillPanel, 4, "image");

    yuDisplayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    yuDisplayer.setImage("7175", "羽")
    yuDisplayer.setDouble("rate", "数量", "yu", "num", "numPerSec")
    yuDisplayer.setSingle("delay", "延迟", "yu", "delay")
    yuDisplayer.setSingle("int", "HPS", "yu", "HPS")
    yuDisplayer.setSingle("percent", "有效比例", "yu", "effRate")
    yuDisplayer.export(skillPanel, 5, "image");

    info1Displayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    info1Displayer.setSingle("int", "相依数量", "xiangyi", "num")
    info1Displayer.setSingle("int", "相依HPS", "xiangyi", "HPS")
    info1Displayer.setSingle("percent", "沐风覆盖率", "mufeng", "cover")
    info1Displayer.export(skillPanel, 6, "text");

    info2Displayer = new SingleSkillDisplayer(resObj.skill, rankObj);
    info2Displayer.setSingle("int", "APS估算", "general", "APS")
    info2Displayer.setSingle("int", "桑柔DPS", "general", "SangrouDPS")
    info2Displayer.setSingle("int", "庄周梦DPS", "general", "ZhuangzhouDPS")
    info2Displayer.setSingle("int", "玉简DPS", "general", "YujianDPS")
    info2Displayer.setSingle("percent", "战斗效率", "general", "efficiency")
    info2Displayer.export(skillPanel, 7, "text");
}

$('.stat-rank').on('mouseout', function(e) {
    var target = $(e.target);
    target.removeClass("highlight");
    $('.float-window').addClass("hidden");
});

$('.stat-rank').on('mouseover', function(e) {
    var target = $(e.target);
    target.addClass("highlight");
    var num = parseInt(target.attr("num"));
    var percent = parseInt(target.attr("percent"));

    $('.float-window').removeClass("hidden");
    var res = getMousePos(event);
    $('.float-window').css("left", (res.x) + "px");
    $('.float-window').css("top", (res.y) + "px");
    $('.fw-content').html("排名：" + percent + "%<br/>人数：" + num);
    $('.fw-title').html("");
});

function getMousePos(event) {
      var e = event || window.event;
      return {x:e.clientX,y:e.clientY}
}

//part 6

battleTime = resObj.overall.sumTime
battleTimePixels = parseInt(battleTime / 100)
var canvas=document.getElementById('replay-timeline');
var ctx=canvas.getContext('2d');
canvas.height = 40;
canvas.width = battleTimePixels;

// 绘制主时间轴
ctx.strokeStyle ="#000000";
ctx.lineWidth = 1;
ctx.strokeRect(0,0,battleTimePixels,40);
ctx.stroke();
nowt = 0;

if (occ == "xiangzhi") {
    if (resObj.replay.heatType){
        if (resObj.replay.heatType == "meihua"){
            nowTimePixel = 0
            for (i in resObj.replay.heat.timeline) {
                var line = resObj.replay.heat.timeline[i];
                ctx.fillStyle = "rgb(" + parseInt(255 - (255 - 100) * line / 100) + "," +
                                         parseInt(255 - (255 - 250) * line / 100) + "," +
                                         parseInt(255 - (255 - 180) * line / 100) + ")";
                ctx.fillRect(nowTimePixel, 1, 5, 39);
                nowTimePixel += 5;
            }
        }
        else if (resObj.replay.heatType == "hot"){
            yPos = [1, 9, 17, 25, 33, 39];
            for (var j = 0; j < 5; j++) {
                nowTimePixel = 0;
                for (i in resObj.replay.heat.timeline[j]) {
                    var line = resObj.replay.heat.timeline[j][i];
                    if (line == 0)
                        ctx.fillStyle = "#ff7777";
                    else {
                        ctx.fillStyle = "rgb(" + parseInt(255 - (255 - 100) * line / 100) + "," +
                                                 parseInt(255 - (255 - 250) * line / 100) + "," +
                                                 parseInt(255 - (255 - 180) * line / 100) + ")";
                    }
                    ctx.fillRect(nowTimePixel, yPos[j], 5, yPos[j+1] - yPos[j]);
                    nowTimePixel += 5;
                }
            }
        }
    }
}

ctx.fillStyle = "#000000";
while (nowt < battleTime) {
    nowt += 10000;
    text = parseTime(nowt / 1000);
    pos = parseInt(nowt / 100);
    ctx.font="12px Arial";
    ctx.fillText(text, pos, 26);
}

startTime = resObj.replay.startTime
painter = $('#replay-paint')
// 绘制常规技能轴

var stack = 3;  // 堆叠数量，TODO后续改成可在页面中修改
var j = -1;
var lastName = "";
var lastStart = 0;
l = resObj.replay.normal.length;
var stackHeal = 0;
var stackHealEff = 0;
var stackNum = 0;
for (var i = 0; i <= l; i++) {
    if (i == l) {
        record = {"skillname": "Final", "start": 999999999999, heal: 0, healEff: 0, num: 0};
    } else {
        record = resObj.replay.normal[i];
        stackHeal += resObj.replay.normal[i].heal;
        stackHealEff += resObj.replay.normal[i].healeff;
        stackNum += resObj.replay.normal[i].num;
    }
    if (record.skillname != lastName || record.start - lastStart > 3000) {
        if (j == -1) {
            j = i;
            lastName = record.skillname;
            lastStart = record.start;
            continue;
        }
        if (i - j >= stack) {
            // 进行堆叠显示
            var record_first = resObj.replay.normal[j];
            var record_last = resObj.replay.normal[i-1];
            posStart = parseInt((record_first.start - startTime) / 100);
            if (posStart < 0) {
                posStart = 0;
            }
            posLength = parseInt((record_last.start + record_last.duration - record_first.start) / 100);
            var singleSkill = $("<div></div>");
            singleSkill.addClass("skill-block");
            singleSkill.appendTo(painter);
            var img = $("<img src=../static/icons/" + record_last.iconid + ".png>");
            img.addClass("skill-image");
            img.appendTo(singleSkill);
            if (posLength >= 20) {
                var block = $("<div></div>");
                block.addClass("skill-time");
                block.addClass("xiangzhi");
                if (posLength >= 30) {
                    block.html("*" + (i-j));
                }
                block.css("width", (posLength - 20) + "px");
                block.appendTo(singleSkill);
            }
            singleSkill.css("top", "70px");
            singleSkill.css("left", posStart + "px");

            singleSkill.attr("skillname", record_last.skillname);
            singleSkill.attr("heal", stackHeal);
            singleSkill.attr("healeff", stackHealEff);
            singleSkill.attr("num", stackNum);
            singleSkill.addClass("skill-active");

        } else {
            // 进行独立显示
            for (var k = j; k < i; k++) {
                var record_single = resObj.replay.normal[k];
                posStart = parseInt((record_single.start - startTime) / 100);
                if (posStart < 0) {
                    posStart = 0;
                }
                posLength = parseInt(record_single.duration / 100);
                var singleSkill = $("<div></div>");
                singleSkill.addClass("skill-block");
                singleSkill.appendTo(painter);
                var img = $("<img src=../static/icons/" + record_single.iconid + ".png>");
                img.addClass("skill-image");
                img.appendTo(singleSkill);
                singleSkill.css("top", "70px");
                singleSkill.css("left", posStart + "px");

                singleSkill.attr("skillname", record_single.skillname);
                singleSkill.attr("heal", record_single.heal);
                singleSkill.attr("healeff", record_single.healeff);
                singleSkill.attr("num", record_single.num);
                singleSkill.attr("targetName", record_single.targetName);
                singleSkill.addClass("skill-active");
            }
        }
        j = i;
        stackHeal = 0;
        stackHealEff = 0;
        stackNum = 0;
    }
    lastName = record.skillname;
    lastStart = record.start;
}


for (var i in resObj.replay.normal) {
    record = resObj.replay.normal[i];
}
// 绘制特殊技能轴
for (var i in resObj.replay.special) {
    record = resObj.replay.special[i];
    posStart = parseInt((record.start - startTime) / 100);
    if (posStart < 0) {
        posStart = 0;
    }
    posLength = parseInt(record.duration / 100);

    var singleSkill = $("<div></div>");
    singleSkill.addClass("skill-block");
    singleSkill.appendTo(painter);

    var img = $("<img src=../static/icons/" + record.iconid + ".png>");
    img.addClass("skill-image");
    img.appendTo(singleSkill);

    singleSkill.css("top", "90px");
    singleSkill.css("left", posStart + "px");

    singleSkill.attr("skillname", record.skillname);
    singleSkill.attr("heal", record.heal);
    singleSkill.attr("healeff", record.healeff);
    singleSkill.attr("num", record.num);
    singleSkill.attr("targetName", record.targetName);
    singleSkill.addClass("skill-active");
}
// 绘制点名轴
for (var i in resObj.replay.call) {
    record = resObj.replay.call[i];
    posStart = parseInt((record.start - startTime) / 100);
    if (posStart < 0) {
        if (posStart < -10) {
            continue;
        }
        posStart = 0;
    }
    posLength = parseInt(record.duration / 100);

    var singleSkill = $("<div></div>");
    singleSkill.addClass("skill-block");
    singleSkill.appendTo(painter);

    var img = $("<img src=../static/icons/" + record.iconid + ".png>");
    img.addClass("skill-image");
    img.appendTo(singleSkill);

    if (posLength >= 20) {
        var block = $("<div></div>");
        block.addClass("skill-time");
        block.addClass("boss");
        if (posLength >= 30) {
            block.html(record.skillname);
        }
        block.css("width", (posLength - 20) + "px");
        block.appendTo(singleSkill);
    }

    singleSkill.css("top", "90px");
    singleSkill.css("left", posStart + "px");

    singleSkill.attr("skillname", record.skillname);
    singleSkill.addClass("skill-active");
}
// 绘制环境轴
for (var i in resObj.replay.environment) {
    record = resObj.replay.environment[i];
    posStart = parseInt((record.start - startTime) / 100);
    if (posStart < 0) {
        if (posStart < -10) {
            continue;
        }
        posStart = 0;
    }
    posLength = parseInt(record.duration / 100);

    var singleSkill = $("<div></div>");
    singleSkill.addClass("skill-block");
    singleSkill.appendTo(painter);

    var img = $("<img src=../static/icons/" + record.iconid + ".png>");
    img.addClass("skill-image");
    img.appendTo(singleSkill);

    if (posLength >= 20) {
        var block = $("<div></div>");
        block.addClass("skill-time");
        block.addClass("boss");
        if (posLength >= 30) {
            var text = record.skillname;
            if (record.num > 1) {
                text += "*" + record.num;
            }
            block.html(text);
        }
        block.css("width", (posLength - 20) + "px");
        block.appendTo(singleSkill);
    }

    singleSkill.css("top", "10px");
    singleSkill.css("left", posStart + "px");

    singleSkill.attr("skillname", record.skillname);
    singleSkill.addClass("skill-active");
}

$('.skill-active').on('mouseout', function(e) {
    var target = $(e.target);
    target = target.parent();
    target.removeClass("highlight");
    $('.float-window').addClass("hidden");
});

$('.skill-active').on('mouseover', function(e) {
    var target = $(e.target);
    target = target.parent();
    target.addClass("highlight");
    var num = parseInt(target.attr("num"));
    var percent = parseInt(target.attr("percent"));

    $('.float-window').removeClass("hidden");
    var res = getMousePos(event);
    $('.float-window').css("left", (res.x) + "px");
    $('.float-window').css("top", (res.y) + "px");
    var text = "";
    if (target.attr("skillname") != undefined)
        $('.fw-title').html(target.attr("skillname"));
    else
        $('.fw-title').html("");
    if (target.attr("heal") != undefined)
        text += "治疗量：" + target.attr("heal") + "<br/>";
    if (target.attr("healeff") != undefined)
        text += "有效治疗量：" + target.attr("healeff") + "<br/>";
    if (target.attr("num") != undefined)
        text += "数量：" + target.attr("num") + "<br/>";
    if (target.attr("targetName") != undefined)
        text += "目标：" + target.attr("targetName") + "<br/>";
    $('.fw-content').html(text);
});

//part 7

var table=$("#data-7-t");
for (var i in resObj.dps.table){
    var tr = $("<tr></tr>");
    tr.appendTo(table);
    var td = $("<td>"+resObj.dps.table[i].name+"</td>");
    td.addClass("occ-"+resObj.dps.table[i].occ)
    td.appendTo(tr);
    var td = $("<td>"+resObj.dps.table[i].damage+"</td>");
    td.appendTo(tr);
    var td = $("<td>"+parseCent(resObj.dps.table[i].shieldRate)+"</td>");
    td.appendTo(tr);
    var td = $("<td>"+resObj.dps.table[i].shieldBreak+"</td>");
    td.appendTo(tr);
}

//part 8

if (resObj.score.available) {

    scoreA = resObj.score.scoreA;
    resA = getLvl(scoreA);
    $('#data-8-1a').html(scoreA);
    $('#data-8-1b').html(resA[0]);
    $('#data-8-1a').css("color", resA[1]);
    $('#data-8-1b').css("color", resA[1]);

    scoreB = resObj.score.scoreB;
    resB = getLvl(scoreB);
    $('#data-8-2a').html(scoreB);
    $('#data-8-2b').html(resB[0]);
    $('#data-8-2a').css("color", resB[1]);
    $('#data-8-2b').css("color", resB[1]);

    scoreC = resObj.score.scoreC;
    resC = getLvl(scoreC);
    $('#data-8-3a').html(scoreC);
    $('#data-8-3b').html(resC[0]);
    $('#data-8-3a').css("color", resC[1]);
    $('#data-8-3b').css("color", resC[1]);

    score = resObj.score.sum;
    res = getLvl(score);
    $('#data-8-4a').html(score);
    $('#data-8-4b').html(res[0]);
    $('#data-8-4a').css("color", res[1]);
    $('#data-8-4b').css("color", res[1]);

    $('#data-8-res').html(res[2]);
    $('#data-8-res').css("color", res[1]);
}
else {
    $('#data-8-t').addClass("hidden");
    $('#data-8-res').addClass("hidden");
    $('#data-8-h').removeClass("hidden");
}

//part 9

$('#ad-id').html(resObj.overall.shortID);