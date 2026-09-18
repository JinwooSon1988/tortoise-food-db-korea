(() => {
  const AUDIT = '../../data/species_evidence_primary_source_audit_v56.json';
  const LINKAGE = '../../data/species_evidence_linkage_v56.json';
  const id = location.pathname.match(/\/plant\/([^/]+)\/?$/)?.[1];
  if (!id) return;

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const get = async u => { const r = await fetch(u); if (!r.ok) throw new Error(u); return r.json(); };

  Promise.all([get(AUDIT), get(LINKAGE)]).then(([audit, linkage]) => {
    const link = (linkage.links || []).find(x => x.food_id === id);
    if (!link) return;
    const rows = (audit.records || []).filter(x => x.asset === link.asset);
    if (!rows.length) return;

    const verified = rows.filter(x => x.status === 'verified_primary');
    const held = rows.filter(x => x.status !== 'verified_primary');
    const gap = link.exact_ibera_gap || link.exact_species_gap || '';

    const section = document.createElement('section');
    section.className = 'card evidence-detail-v56';
    section.innerHTML =
      '<h2>검증된 상세 근거</h2>' +
      '<p class="small">원문 대조를 통과한 기록만 이름을 공개한다. 야생 섭식·사육 중 사용 기록은 안전성 시험이나 급여량 처방이 아니다.</p>' +
      (verified.length ? '<ul>' + verified.map(r =>
        '<li><b>원문 확인</b> · ' + esc(r.verification) + '<br><span class="small">' + esc(r.scope) + '</span></li>'
      ).join('') + '</ul>' : '<p>현재 공개 가능한 원문 검증 기록이 없다.</p>') +
      (gap ? '<div class="notice"><b>적용 한계</b><br>' + esc(gap) + '</div>' : '') +
      '<div class="notice"><b>공개 해석 규칙</b><br>' + esc(link.public_detail_rule) + '</div>' +
      (held.length ? '<p class="small">추가로 ' + held.length + '건은 출처 미확인 또는 원문 충돌로 공개 근거에서 보류 중이다.</p>' : '');
    const nav = document.querySelector('nav');
    (nav || document.body).before(section);
  }).catch(() => {});
})();
