#!/usr/bin/env python3
"""Validate and summarize research-source joins without upgrading any source to a feeding recommendation."""
import argparse,json,pathlib,collections,urllib.parse
def main():
 p=argparse.ArgumentParser();p.add_argument('--index',default='data/research_source_leads_index.json');p.add_argument('--report',default='data/research_coverage_report.json');p.add_argument('--out',default='data/research_quality_gate.json');a=p.parse_args()
 data=json.loads(pathlib.Path(a.index).read_text(encoding='utf-8'))
 taxa=data.get('taxa',{});issues=[];counts=collections.Counter();unique_sources=set()
 for taxon,item in taxa.items():
  if not taxon.startswith('gbif:'):issues.append({'taxon':taxon,'error':'invalid_taxon_id'})
  for kind in ('literature_leads','community_mentions'):
   for lead in item.get(kind,[]):
    counts[kind]+=1
    if lead.get('feeding_safety_status')!='unassessed':issues.append({'taxon':taxon,'error':'unreviewed_source_given_safety_status'})
    if kind=='literature_leads' and lead.get('verification')!='search_hit_unreviewed':issues.append({'taxon':taxon,'error':'literature_verification_misrepresented'})
    if kind=='community_mentions' and lead.get('verification')!='community_claim_not_independently_verified':issues.append({'taxon':taxon,'error':'community_verification_misrepresented'})
    url=lead.get('url') if kind=='literature_leads' else lead.get('source_url')
    parsed=urllib.parse.urlparse(url or '')
    if parsed.scheme!='https' or not parsed.netloc:issues.append({'taxon':taxon,'error':'invalid_or_missing_source_url'})
    else:unique_sources.add(url)
 report={'passed':not issues,'taxa_with_source_leads':sum(bool(x.get('literature_leads') or x.get('community_mentions')) for x in taxa.values()),'literature_leads':counts['literature_leads'],'community_mentions':counts['community_mentions'],'unique_source_urls':len(unique_sources),'errors':issues[:100],'error_count':len(issues),'safety_grades_assigned':0,'disclaimer':'Source-lead coverage is not evidence of safe feeding.'}
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='errors'},ensure_ascii=False))
 if issues:raise SystemExit(1)
if __name__=='__main__':main()
