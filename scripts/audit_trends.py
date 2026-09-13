from pathlib import Path
R=Path(__file__).resolve().parents[1]
h=(R/'trends/index.html').read_text(encoding='utf-8'); home=(R/'index.html').read_text(encoding='utf-8'); sw=(R/'sw.js').read_text(encoding='utf-8')
checks={'trend_page_exists':bool(h),'uses_growth_storage':"tfd_growth_v1" in h,'uses_weekly_storage':"tfd_weekly_v1" in h,'profile_scoped':"x.profile_id===p.id" in h,'has_90_day':"최근 90일" in h and "-89" in h,'has_all_time':"전체기간" in h,'weight_chart':"weight_g" in h,'scl_chart':"scl_mm" in h,'causality_warning':"원인·효과를 의미하지 않" in h,'no_health_score':"자동 판정하지 않는다" in h,'home_links_trends':'./trends/' in home,'home_links_growth':'./growth/' in home,'pwa_has_trends':'./trends/' in sw,'pwa_v51':"tfd-v51-stable-1" in sw}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Trends audit failed: '+', '.join(failed))
print('Long-term trends audit PASS')
