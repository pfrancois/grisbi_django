/* coding: utf-8 */

var currentEditField = "";
var editorOriginalValue = "";
var currentEditor = "";

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
	if (currentEditor !== "") {
		currentEditor.style.visibility = "hidden";
		editorOriginalValue = "";
		currentEditField = "";
		currentEditor = "";
		window.scroll(0, 0);
	}
}

function startEditor(editorId, fieldId) {
	var posy;
	if (currentEditor !== "") {
		closeCurrentEditor();
	} else {
		currentEditor = document.getElementById(editorId);
		currentEditField = document.getElementById(fieldId);
		posy = findPosY(currentEditField);
		currentEditor.style.top = (posy + 25) + "px";
		currentEditor.style.visibility = "visible";
		editorOriginalValue = currentEditField.innerHTML;
		window.scroll(0, posy);
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
 * @param {string} mode "input" ou "inline"
 * @return {string} le calendrier affiche
 */
function buildCal(d, m, y, cM, cH, cDW, cD, brdr, mode) {
	var  i, s;
	var mn = ['Janvier', 'F&eacute;vrier', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Ao&ucirc;t', 'Septembre', 'Octobre', 'Novembre', 'D&eacute;cembre'];
	var dim = [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

	var oD = new Date(y, m - 1, 1); //DD replaced line to fix date bug when current day is 31st
	oD.od = oD.getDay(); //DD replaced line to fix date bug when current day is 31st
	if (oD.od===0){oD.od=7;}
	var todaydate = new Date(); //DD added
	var scanfortoday = (y === todaydate.getFullYear() && m === todaydate.getMonth() + 1) ? todaydate.getDate() : 0; //DD added

	var previousYear = y;
	var nextYear = y;
	var previousMonth = m - 1;
	if (m === 1) {
		previousMonth = 12;
		previousYear = previousYear - 1;
	}
	var nextMonth = m + 1;
	if (m === 12) {
		nextMonth = 1;
		nextYear = nextYear + 1;
	}
	//gestion du nnombre de jour pour fevrier
	dim[1] = (((oD.getFullYear()%100 !== 0) && (oD.getFullYear()%4 === 0)) || (oD.getFullYear()%400 === 0)) ?29:28;
	var t = '<div class="'+cM+'"><table class="'+cM+'" cols="7" cellpadding="0" border="'+brdr+'" cellspacing="0"><tr align="center">';
	t+= '<td class="boutton"><a href="javascript:calendarSelectMonth(' + previousMonth + ', ' + previousYear + ')">&lt;&lt;</a></td><td colspan="5" align="center" class="'+cH+'">'+mn[m - 1]+' - '+y+'</td><td class=boutton><a href="javascript:calendarSelectMonth(' + nextMonth + ', ' + nextYear + ')">&gt;&gt;</a></td></tr><tr align="center">';
	for(s = 0;s<7;s++) {t+= '<td class="' + cDW + '">' + "LMMJVSD".substr(s, 1) + '</td>';}
	t+= '</tr><tr align="center">';
	for(i = 1;i <= 42;i++) {
		var x = '&nbsp;';
		if ((i-oD.od >= 0) && (i-oD.od < dim[m - 1])) {
			var day= (i-oD.od +1);
			x = day;
			if (x === scanfortoday) { //DD added
				x = '<span id="calendartoday">'+x+'</span>'; //DD added
				x = '<a href="javascript:calendarSelectDate('+day+', '+m+', '+y+')">'+x+'</a>';
			}else{
				x = '<a href="javascript:calendarSelectDate('+day+', '+m+', '+y+')">'+x+'</a>';
			}
		}
		t+= '<td class="'+cD+'">'+x+'</td>';
		if(((i)%7 === 0) && ( i < 36)) {
			t+= '</tr><tr align="center">';
		}
	}
	t+= '</tr><tr><td colspan="7" class="boutton"><a href="javascript:closeCurrentEditor()">Annuler</a></td></table></div>';
	return t;
}


function editDate(fieldId) {
	var todaydate = new Date();
	var posy;
	var curyear;
	var curmonth;
	var curday;
	if (currentEditor !== "") {
		closeCurrentEditor();
	}
	else{
		currentEditor = document.getElementById("editDateId");
		currentEditField = document.getElementById(fieldId);
		posy = findPosY(currentEditField);
		editorOriginalValue = currentEditField.value;
		window.scroll(0, posy);
		curyear = editorOriginalValue.substring(4, 8)*1;
		curmonth = editorOriginalValue.substring(2, 4)*1;
		curday = editorOriginalValue.substring(0, 2)*1;
		if (editorOriginalValue.length<8){
			curyear = todaydate.getFullYear()*1;
			curmonth = todaydate.getMonth()*1;
			curday = todaydate.getDay()*1;
		}
		currentEditor.innerHTML = buildCal(curday, curmonth , curyear, "calendarmain", "calendarmonth", "calendardaysofweek", "calendardays", 2);
		currentEditor.style.top = (posy+25)+ "px";
		currentEditor.style.visibility = "visible";
  }
}


function calendarSelectMonth(month, year) {
  currentEditor.innerHTML = buildCal(0, month , year, "calendarmain", "calendarmonth", "calendardaysofweek", "calendardays", 2);
}

function calendarSelectDate(day, month, year) {
  if (day < 10) {day = "0"+day;}
  if (month < 10) {month = "0"+month;}
   currentEditField.value = ""+day+month+year;
  closeCurrentEditor();
}

