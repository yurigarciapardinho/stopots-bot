() => {
  const visible = e => {
    if (!e || !e.getClientRects().length) return false;
    for (let p=e; p; p=p.parentElement) {
      const s=getComputedStyle(p);
      if (p.hidden || p.getAttribute('aria-hidden')==='true' || s.display==='none' || s.visibility==='hidden') return false;
    }
    return true;
  };
  const txt = e => (e?.innerText || e?.textContent || '').trim();
  const q = (s,root=document) => [...root.querySelectorAll(s)].filter(visible);
  const active = e => {
    if (!visible(e)) return false;
    for(let p=e;p;p=p.parentElement) if(+getComputedStyle(p).opacity===0) return false;
    return true;
  };
  const ref = e => {
    if (e.id && document.querySelectorAll('#'+CSS.escape(e.id)).length===1) return '#'+CSS.escape(e.id);
    const parts=[];
    for (let p=e; p && p!==document.documentElement; p=p.parentElement) {
      const siblings=[...p.parentElement.children].filter(x=>x.tagName===p.tagName);
      parts.unshift(p.tagName.toLowerCase()+':nth-of-type('+(siblings.indexOf(p)+1)+')');
    }
    return 'html > '+parts.join(' > ');
  };
  const headings=q('h1,h2,h3,h4,h5,h6,legend').filter(active);
  const buttons=q('button').filter(active);
  const control = text => {
    const matches=buttons.filter(b=>txt(b)===text);
    return matches.length===1 ? {ref:ref(matches[0]),enabled:!matches[0].disabled && matches[0].getAttribute('aria-disabled')!=='true'} : null;
  };
  const reviewHeading=headings.filter(h=>/VALIDE AS RESPOSTAS\s+\d+\s*\/\s*\d+/.test(txt(h)));
  const resultHeadings=headings.filter(h=>/^RANKING\s+(DA\s+RODADA|FINAL)/.test(txt(h)));
  const finals=resultHeadings.filter(h=>/^RANKING\s+FINAL/.test(txt(h)));
  const resultHeading=finals.length===1?finals:resultHeadings;
  const writingHeading=headings.filter(h=>txt(h)==='PREENCHA AS CATEGORIAS');
  const inputs=q('input[id^="inputText-"]');
  const bodyText=document.body.innerText;
  const round=bodyText.match(/RODADAS:\s*(\d+)\s*\/\s*(\d+)/);
  const letter=bodyText.match(/RODADAS:\s*\d+\s*\/\s*\d+\s*([A-Z])\b/);
  let phase='DESCONHECIDO', review_theme=null, groups=[], ranking=null;
  let review_index=null, review_total=null;
  let result_round=null, result_total=null;
  if (resultHeading.length===1) {
    phase=/RANKING\s+FINAL/.test(txt(resultHeading[0]))?'RESULTADO_PARTIDA':'RESULTADO_RODADA';
    const m=txt(resultHeading[0]).match(/(\d+)\s*\/\s*(\d+)/);
    if(m) {result_round=+m[1];result_total=+m[2];}
    // O adaptador só extrai linhas de ranking de um painel que contém o título.
    let root=resultHeading[0].closest('.ranking') || resultHeading[0].parentElement;
    while(root!==document.body && !root.querySelector('.userRkg')) root=root.parentElement;
    const rows=q('.userRkg',root).filter(active).map(e=>({ref:ref(e),name:txt(e.querySelector('.nick')),points:txt(e.querySelector('.points'))}));
    ranking={rows,round_index:result_round,semantic:phase==='RESULTADO_PARTIDA'?'total_partida':'rodada'};
  } else if (reviewHeading.length===1) {
    phase='REVISAO';
    const m=txt(reviewHeading[0]).match(/(\d+)\s*\/\s*(\d+)/);
    review_index=+m[1]; review_total=+m[2];
    let root=reviewHeading[0].parentElement;
    while(root!==document.body && !q('label[for]',root).some(l=>document.getElementById(l.htmlFor)?.type==='checkbox')) root=root.parentElement;
    groups=q('label[for]',root).map(l=>({label:l,input:document.getElementById(l.htmlFor)}))
      .filter(x=>x.input?.type==='checkbox')
      .map(x=>({ref:ref(x.input),label_ref:ref(x.label),text:txt(x.label),checked:x.input.checked,enabled:!x.input.disabled}));
    const themes=q('h2,h3,h4,legend',root).filter(h=>h!==reviewHeading[0]);
    if (themes.length===1) review_theme=txt(themes[0]);
  } else if(writingHeading.length===1 && inputs.length && round && letter) phase='ESCRITA';
  else if(q('input[type="password"]').length || (control('ENTRAR') && /Você foi convidado/.test(bodyText))) phase='ENTRANDO';
  else if(control('CRIAR SALA')) phase='INICIO';
  else if(headings.some(h=>/^CATEGORIAS \(\d+\)/.test(txt(h))) && /CONFIGURAÇÕES/.test(bodyText)) phase='SALA';
  const fields=phase==='ESCRITA'?inputs.map(e=>({ref:ref(e),label:[...(e.labels||[])].map(txt).join(' ') || txt(e.closest('fieldset')?.querySelector('legend')),
    value:e.value,editable:!e.disabled&&!e.readOnly,max_length:e.maxLength>=0?e.maxLength:null})):[];
  const selected=q('select').map(e=>({options:[...e.options].map(x=>txt(x)),value:txt(e.selectedOptions[0]),disabled:e.disabled}));
  const stopSelect=selected.find(e=>e.options.includes('Padrão') && e.options.includes('Maioria'));
  const timeSelect=selected.find(e=>e.options.includes('Mais lento'));
  const letters=q('label[for]').filter(e=>/^[A-Z]$/.test(e.htmlFor) && document.getElementById(e.htmlFor)?.checked).map(e=>e.htmlFor);
  const disconnected=q('*').some(e=>e.children.length===0 && /Conexão perdida|foi removido por inatividade|Você foi desconectado/i.test(txt(e)));
  return {phase,room_key:/\/pt\/\d+\/?$/.test(location.pathname)?location.pathname:null,
    round_index:phase==='RESULTADO_RODADA'?result_round:(round?+round[1]:null),total_rounds:result_total||(round?+round[2]:null),
    letter:letter?letter[1]:null,fields,groups,review_theme,review_index,review_total,
    stop:phase==='ESCRITA'?control('STOP!'):null,confirm:phase==='REVISAO'?control('AVALIAR'):null,
    proceed:phase==='RESULTADO_RODADA'?control('ESTOU PRONTO'):null,
    connected:!disconnected,rules:{stop_mode:stopSelect?.value||null,time_mode:timeSelect?.value||null,
      letters,category_pool:q('.listThemes .theme').map(txt),is_host:stopSelect?!stopSelect.disabled:null},ranking};
}
