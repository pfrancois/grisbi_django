/* coding: utf-8 */
/**
 *
 * @param index_selected
 * @param id_select
 * @param id_texte
 * @param css_ok
 * @param id_num
 */
function verifie_numero_visible_selon_css(index_selected, id_select, id_texte, css_ok, id_num) {
	var sel = document.getElementById(id_select);
	var numero = document.getElementById(id_texte);
	var verif = sel.options[index_selected].className;
	numero.value = '';
	document.getElementById(id_num).value = '';
	if (verif === css_ok) {
		numero.style.display = "inline";
	} else {
		numero.style.display = 'none';
	}
}

/**
 *
 * @param index_selected
 * @param id_select
 * @param id_span_texte
 * @param texte_ok
 * @param id_texte
 */
function verifie_numero_visible_selon_texte(index_selected, id_select, id_span_texte, texte_ok, id_texte) {
	var sel = document.getElementById(id_select);
	var numero = document.getElementById(id_span_texte);
	var verif = sel.value;
	document.getElementById(id_texte).value = '';
	if (verif === texte_ok) {
		numero.style.display = "inline";
	} else {
		numero.style.display = 'none';

	}
}

//c'est juste la fonction d'au dessus mais sans l'effacage de la cellule

function select_type_init() {
	var sel = document.getElementById('moyen');
	var numero = document.getElementById('num_chq');
	var verif = sel.options[sel.selectedIndex].className;
	if (verif === 'typeAvecNumero') {
		numero.style.display = "inline";
	} else {
		numero.style.display = 'none';
	}
}
