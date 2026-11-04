"""Contract tests for the shareable skill's offline pack audit."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'.agents/skills/policy-eval-author/scripts/audit_policy_pack.py'


def run_audit(pack, *extra):
    result=subprocess.run([sys.executable,str(SCRIPT),'--repo',str(ROOT),'--pack',str(pack),*extra],capture_output=True,text=True)
    return result.returncode,json.loads(result.stdout)


def fixture_pack():
    return json.loads((ROOT/'evals/fixtures/policy_additions.json').read_text(encoding='utf-8'))


def save(tmp_path,pack):
    path=tmp_path/'pack.json';path.write_text(json.dumps(pack),encoding='utf-8');return path


def test_skill_audits_additions_without_changing_catalogue():
    catalogue=ROOT/'agent/data/policies.json'
    before=catalogue.read_bytes()
    code,result=run_audit(ROOT/'evals/fixtures/policy_additions.json','--baseline','agent/data/policies.json')
    assert code==0 and result['combined_policies']==18 and result['rule_examples_checked']==7
    assert catalogue.read_bytes()==before


def test_skill_rejects_wrong_boundary_expectation(tmp_path):
    pack=fixture_pack()[:1]
    pack[0]['tests'][1]['expected']='prohibited'
    code,result=run_audit(save(tmp_path,pack))
    assert code==1 and any('disagrees' in e for e in result['errors'])


def test_skill_rejects_baseline_id_collision(tmp_path):
    pack=fixture_pack()[:1];pack[0]['id']='prohibited-perfume'
    code,result=run_audit(save(tmp_path,pack),'--baseline','agent/data/policies.json')
    assert code==1 and any('collide' in e for e in result['errors'])


def test_skill_flags_operator_requiring_implementation(tmp_path):
    pack=fixture_pack()[:1];pack[0]['rule']['conditions'][0]['op']='between'
    code,result=run_audit(save(tmp_path,pack))
    assert code==1 and any('unsupported operator' in e for e in result['errors'])


def test_skill_flags_unextractable_facts(tmp_path):
    pack=fixture_pack()[:1]
    pack[0]['rule']['required'].append('temperature_c')
    code,result=run_audit(save(tmp_path,pack))
    assert code==1 and any('extractor' in e for e in result['errors'])


def test_skill_checks_case_ids_against_existing_suite(tmp_path):
    path=tmp_path/'cases.jsonl'
    original=(ROOT/'evals/cases.jsonl').read_text(encoding='utf-8').splitlines()[0]
    path.write_text(original+'\n',encoding='utf-8')
    code,result=run_audit(ROOT/'evals/fixtures/policy_additions.json','--cases',str(path))
    assert code==2 and any('Duplicate case ID' in e for e in result['errors'])
