/* coding: utf-8 */
var DATE_FORMAT_REGXES = {
    'Y':new RegExp('^-?[0-9]+'),
    'd':new RegExp('^[0-9]{1,2}'),
    'm':new RegExp('^[0-9]{1,2}'),
    'H':new RegExp('^[0-9]{1,2}'),
    'M':new RegExp('^[0-9]{1,2}')
};


/*
 * _parseData does the actual parsing job needed by `strptime`
 */
function _parseDate(datestring, format) {
    var parsed = {};
    for (var i1 = 0, i2 = 0; i1 < format.length; i1++, i2++) {
        var c1 = format[i1];
        var c2 = datestring[i2];
        if ('%' == c1) {
            c1 = format[++i1];
            var data = DATE_FORMAT_REGXES[c1].exec(datestring.substring(i2));
            if (!data.length) {
                return null;
            }
            data = data[0];
            i2 += data.length - 1;
            var value = parseInt(data, 10);
            if (isNaN(value)) {
                return null;
            }
            parsed[c1] = value;
            continue;
        }
        if (c1 != c2) {
            return null;
        }
    }
    return parsed;
}

/*
 * basic implementation of strptime. The only recognized formats
 * defined in _DATE_FORMAT_REGEXES (i.e. %Y, %d, %m, %H, %M)
 */
function strptime(datestring, format) {

    var parsed = _parseDate(datestring, format);
    if (!parsed) {
        return null;
    }
    // create initial date (!!! year=0 means 1900 !!!)
    var date = new Date(0, 0, 1, 0, 0);
    date.setFullYear(0);
    // reset to year 0
    if (parsed.Y) {
        date.setFullYear(parsed.Y);
    }
    if (parsed.m) {
        if (1 > parsed.m || 12 < parsed.m) {
            return null;
        }
        // !!! month indexes start at 0 in javascript !!!
        date.setMonth(parsed.m - 1);
    }
    if (parsed.d) {
        if (1 > parsed.m || 31 < parsed.m) {
            return null;
        }
        date.setDate(parsed.d);
    }
    if (parsed.H) {
        if (0 > parsed.H || 23 < parsed.H) {
            return null;
        }
        date.setHours(parsed.H);
    }
    if (parsed.M) {
        if (0 > parsed.M || 59 < parsed.M) {
            return null;
        }
        date.setMinutes(parsed.M);
    }
    return date;
}

var currentEditField = "";
var editorOriginalValue = "";
var currentEditor = "";
var format_date = "";

function findPosY(obj) {
    var o = obj;
    var curtop = 0;
    if (o.offsetParent) {
        while (1) {
            curtop += o.offsetTop;
            if (!o.offsetParent) {
                break;
            }
            o = o.offsetParent;
        }
    } else if (o.y) {
        curtop += o.y;
    }
    return curtop;
}

function findPosX(obj) {
    var curleft = 0;
    if (obj.offsetParent) {
        while (1) {
            curleft += obj.offsetLeft;
            if (!obj.offsetParent) {
                break;
            }
            obj = obj.offsetParent;
        }
    } else if (obj.x) {
        curleft += obj.x;
    }
    return curleft;
}

function closeCurrentEditor() {
    if ("" !== currentEditor) {
        currentEditor.style.visibility = "hidden";
        editorOriginalValue = "";
        currentEditField = "";
        currentEditor = "";
        window.scrollTo(0, 0);
    }
}

function startEditor(editorId, fieldId) {
    var posy;
    if ("" !== currentEditor) {
        closeCurrentEditor();
    } else {
        currentEditor = document.getElementById(editorId);
        currentEditField = document.getElementById(fieldId);
        posy = findPosY(currentEditField);
        currentEditor.style.top = (posy + 25) + "px";
        currentEditor.style.visibility = "visible";
        editorOriginalValue = currentEditField.innerHTML;
        window.scrollTo(0, posy);
    }
}

/*-----------------------
 * Basic Calendar-By Brian Gosselin at http://scriptasylum.com/bgaudiodr/
 * Script featured on Dynamic Drive (http://www.dynamicdrive.com)
 * This notice must stay intact for use
 * Visit http://www.dynamicdrive.com/ for full source code
 ---------------------------------------*/
/**
 * creer effectivement le calendrier
 * @param {int} d
 * @param {int} m
 * @param {int} y
 * @param {string} cM css principale
 * @param {string} cH css du mois
 * @param {string} cDW css de la semaine
 * @param {string} cD css du jour
 * @param {string} brdr css bordure
 * @return {string} le calendrier affiche
 */
function buildCal(d, m, y, cM, cH, cDW, cD, brdr) {
    var i, s;
    var mn = ['Janvier', 'F&eacute;vrier', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Ao&ucirc;t', 'Septembre', 'Octobre', 'Novembre', 'D&eacute;cembre'];
    var dim = [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    var oD = new Date(y, m - 1, 1);
    //DD replaced line to fix date bug when current day is 31st
    oD.od = oD.getDay();
    //DD replaced line to fix date bug when current day is 31st
    if (0 === oD.od) {
        oD.od = 7;
    }
    var todaydate = new Date();
    //DD added
    var scanfortoday = (y === todaydate.getFullYear() && m === todaydate.getMonth() + 1) ? todaydate.getDate() : 0;
    //DD added

    var previousYear = y;
    var nextYear = y;
    var previousMonth = m - 1;
    if (1 === m) {
        previousMonth = 12;
        previousYear -= 1;
    }
    var nextMonth = m + 1;
    if (12 === m) {
        nextMonth = 1;
        nextYear += 1;
    }
    //gestion du nombre de jour pour fevrier
    dim[1] = (((0 !== oD.getFullYear() % 100) && (0 === oD.getFullYear() % 4)) || (0 === oD.getFullYear() % 400)) ? 29 : 28;
    var t = '<div class="' + cM + '"><table class="' + cM + '" cols="7" cellpadding="0" border="' + brdr + '" cellspacing="0"><tr align="center">';
    t += '<td class="boutton"><a href="javascript:calendarSelectMonth(' + previousMonth + ', ' + previousYear + ')">&lt;&lt;</a></td><td colspan="5" align="center" class="' + cH + '">' + mn[m - 1] + ' - ' + y + '</td><td class=boutton><a href="javascript:calendarSelectMonth(' + nextMonth + ', ' + nextYear + ')">&gt;&gt;</a></td></tr><tr align="center">';
    for (s = 0; 7 > s; s++) {
        t += '<td class="' + cDW + '">' + "LMMJVSD".substr(s, 1) + '</td>';
    }
    t += '</tr><tr align="center">';
    for (i = 1; 42 >= i; i++) {
        var x = '&nbsp;';
        if ((0 <= i - oD.od) && (i - oD.od < dim[m - 1])) {
            var day = (i - oD.od + 1);
            x = day;
            if (x === scanfortoday) {//DD added
                x = '<span id="calendartoday">' + x + '</span>';
                //DD added
                x = '<a href="javascript:calendarSelectDate(' + day + ', ' + m + ', ' + y + ')">' + x + '</a>';
            } else {
                x = '<a href="javascript:calendarSelectDate(' + day + ', ' + m + ', ' + y + ')">' + x + '</a>';
            }
        }
        t += '<td class="' + cD + '">' + x + '</td>';
        if ((0 === (i) % 7) && (36 > i)) {
            t += '</tr><tr align="center">';
        }
    }
    t += '</tr><tr class="boutton"><td colspan="7"><a href="javascript:closeCurrentEditor()">Annuler</a></td></table></div>';
    return t;
}

function editDate(fieldId, format) {
    var todaydate = new Date();
    var posy;
    var curyear;
    var curmonth;
    var curday;
    var myDate;
    if (!format) {
        if (document.getElementById(fieldId).value.indexOf('/') != -1) {
            format = "%d/%m/%Y";
        } else {
            format = "%d%m%y";
        }
    }
    format_date = format;
    if ("" !== currentEditor) {
        closeCurrentEditor();
    } else {
        currentEditor = document.getElementById("editDateId");
        currentEditField = document.getElementById(fieldId);
        posy = findPosY(currentEditField);
        editorOriginalValue = currentEditField.value;
        window.scroll(0, posy);
        myDate = strptime(editorOriginalValue, format);
        curyear = myDate.getFullYear();
        curmonth = myDate.getMonth() + 1;
        curday = myDate.getDate();
        currentEditor.innerHTML = buildCal(curday, curmonth, curyear, "calendarmain", "calendarmonth",
                "calendardaysofweek", "calendardays", 2);
        currentEditor.style.top = (posy + 25) + "px";
        currentEditor.style.visibility = "visible";
    }
}

function calendarSelectMonth(month, year) {
    currentEditor.innerHTML = buildCal(0, month, year, "calendarmain", "calendarmonth", "calendardaysofweek",
            "calendardays", 2);
}

function calendarSelectDate(day, month, year) {
    if (10 > day) {
        day = "0" + day;
    }
    if (10 > month) {
        month = "0" + month;
    }
    currentEditField.value = "" + day + "/" + month + "/" + year;
    closeCurrentEditor();
}

function shct_date(offset, fieldId) {
    var d = new Date();
    var day;
    var month;
    d.setDate(d.getDate() + offset);
    currentEditField = document.getElementById(fieldId);
    day = d.getDate();
    if (10 > day) {
        day = "0" + day;
    }
    month = d.getMonth() + 1;
    if (10 > month) {
        month = "0" + month;
    }
    currentEditField.value = "" + day + "/" + month + "/" + (d.getFullYear() * 1);

}