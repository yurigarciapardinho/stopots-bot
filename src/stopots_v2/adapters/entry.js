() => {
  const active = e => {
    if (!e || !e.getClientRects().length) return false;
    for(let p=e;p;p=p.parentElement) {
      const s=getComputedStyle(p);
      if(p.hidden || s.display==='none' || s.visibility==='hidden' || +s.opacity===0) return false;
    }
    return true;
  };
  const text = e => (e.innerText || e.textContent || '').trim();
  const q = (s,r=document) => [...r.querySelectorAll(s)].filter(active);
  const ref = e => {
    if(e.id && document.querySelectorAll('#'+CSS.escape(e.id)).length===1) return '#'+CSS.escape(e.id);
    const a=[];
    for(let p=e;p && p!==document.documentElement;p=p.parentElement) {
      const same=[...p.parentElement.children].filter(x=>x.tagName===p.tagName);
      a.unshift(p.tagName.toLowerCase()+':nth-of-type('+(same.indexOf(p)+1)+')');
    }
    return 'html > '+a.join(' > ');
  };
  const notices=q('.popupSystem:not(.share),[role="alert"],[role="alertdialog"],[aria-modal="true"]');
  let error=null;
  for(const n of notices) {
    const t=text(n);
    if(/senha/i.test(t) && /incorret|inválid|errad|não confere/i.test(t)) error='PASSWORD_REJECTED';
    else if(/sala.*(cheia|existe|encontrada|indisponível)|expuls|inatividade|desconectado/i.test(t)) error='ROOM_UNAVAILABLE';
    else if(q('input[type="password"]',n).some(e=>!e.disabled&&!e.readOnly) ||
      (/Você foi convidado/i.test(t) && q('button',n).some(e=>text(e)==='ENTRAR'))) continue;
    else if(n.matches('.popupSystem,[role="alertdialog"],[aria-modal="true"]')) error='UNKNOWN_NOTICE';
  }
  const passwords=q('input[type="password"]').filter(e=>!e.disabled&&!e.readOnly);
  if(passwords.length>1) return {error:'UNKNOWN_NOTICE'};
  let root=null;
  if(passwords.length===1) {
    root=passwords[0].parentElement;
    while(root && q('button',root).filter(e=>text(e)==='ENTRAR').length!==1) root=root.parentElement;
  } else {
    const invitations=q('h1,h2,h3,h4,p,span,div').filter(e=>/Você foi convidado/i.test(text(e)) &&
      ![...e.children].some(c=>/Você foi convidado/i.test(text(c))));
    if(invitations.length===1) {
      root=invitations[0].parentElement;
      while(root && q('button',root).filter(e=>text(e)==='ENTRAR').length!==1) root=root.parentElement;
    }
  }
  const buttons=root?q('button',root).filter(e=>text(e)==='ENTRAR'&&!e.disabled):[];
  return {error,password:passwords.length===1?ref(passwords[0]):null,
    max_length:passwords.length===1?passwords[0].maxLength:-1,
    button:buttons.length===1?ref(buttons[0]):null};
}
