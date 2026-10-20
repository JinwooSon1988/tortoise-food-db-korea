# 거북밥 GBIF 자료 연결 — Google Colab (무료 CPU)
# 모바일에서 Colab에 새 노트북을 열고 아래 코드를 셀 하나에 붙여넣어 실행하세요.
# GitHub Actions 실행 시간과 GitHub 결제 한도를 사용하지 않습니다.
# 공개 PR 브랜치만 다운로드하며 GitHub 로그인/토큰이 필요하지 않습니다.
# 결과는 Colab 파일 영역에 생성됩니다. 급여 판정이나 운영 사이트는 수정하지 않습니다.

import json, pathlib, subprocess, sys, urllib.request, zipfile, io

REPO = "JinwooSon1988/tortoise-food-db-korea"
BRANCH = "feat/bulk-plant-intake-contract-20261016"
RUN_ID = 38837601795
BASE = pathlib.Path("/content/geobukbap")
BASE.mkdir(parents=True, exist_ok=True)

def get_json(url):
    req = urllib.request.Request(url, headers={"Accept":"application/vnd.github+json", "User-Agent":"geobukbap-colab"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)

# Download the public branch as a ZIP; no git credentials required.
src = f"https://api.github.com/repos/{REPO}/zipball/{BRANCH}"
with urllib.request.urlopen(urllib.request.Request(src,headers={"User-Agent":"geobukbap-colab"}), timeout=120) as resp:
    archive = zipfile.ZipFile(io.BytesIO(resp.read()))
for member in archive.infolist():
    parts = pathlib.PurePosixPath(member.filename).parts
    if len(parts) < 2 or member.is_dir():
        continue
    relative = pathlib.Path(*parts[1:])
    target = BASE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(archive.read(member))

# The GitHub public Actions artifacts API lists the archive IDs.
meta = get_json(f"https://api.github.com/repos/{REPO}/actions/runs/{RUN_ID}/artifacts?per_page=100")
items = [x for x in meta.get("artifacts",[]) if x["name"].startswith("gbif-global-taxonomy-candidates-") and not x.get("expired")]
print("Public artifact entries:", len(items))
if not items:
    raise RuntimeError("GitHub artifact ZIPs cannot be retrieved anonymously or have expired. Upload the two artifact ZIPs into Colab and extract them under research/generated/gbif_batches/<artifact-name>/ instead.")
# Public API artifact archive downloads generally require authentication.
# Never paste a GitHub personal access token into a shared notebook.
batch_dir = BASE / "research/generated/gbif_batches"
batch_dir.mkdir(parents=True,exist_ok=True)
from google.colab import files
print("Upload the two ZIP files downloaded from the GitHub Actions run's Artifacts section.")
uploaded = files.upload()
for filename, raw in uploaded.items():
    if not filename.lower().endswith(".zip"):
        continue
    name = pathlib.Path(filename).stem
    target = batch_dir / name
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for item in z.infolist():
            if pathlib.PurePosixPath(item.filename).name == "gbif_global_taxa_sample.json":
                (target / "gbif_global_taxa_sample.json").write_bytes(z.read(item))
batches = sorted(batch_dir.glob("*/gbif_global_taxa_sample.json"))
if not batches:
    raise RuntimeError("No GBIF batch JSON was found in the uploaded ZIP files.")
out = BASE / "research/generated/gbif_candidate_evidence_join.json"
cmd = [sys.executable,str(BASE / "scripts/join_gbif_candidates_with_evidence.py"),"--batches",*map(str,batches),"--out",str(out)]
subprocess.run(cmd,check=True,cwd=BASE)
result = json.loads(out.read_text(encoding="utf-8"))
print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
files.download(str(out))
