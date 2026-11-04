"""Read-only offline audit of policy packs against this repository's contracts.

Never writes policies, creates gold answers, calls models, or publishes changes.
"""
import argparse
import json
import sys
from pathlib import Path


def audit(repo, pack, baseline=None, cases=None):
    sys.path.insert(0,str(repo))
    from agent.policies import load_policies, evaluate_policy, PolicyStore
    from agent.classifier import TOPICS
    errors=[]
    warnings=[]
    raw=json.loads(pack.read_text(encoding='utf-8-sig'))
    if not isinstance(raw,list):raise ValueError('Policy pack must be a JSON array')
    active=load_policies(pack)
    base=load_policies(baseline) if baseline else []
    collisions={p['id'] for p in active}&{p['id'] for p in base}
    if collisions:errors.append('Addition IDs collide with baseline: '+', '.join(sorted(collisions)))
    combined=base+active
    store=PolicyStore(combined)
    tested=0
    for policy in raw:
        if type(policy.get('version')) is not int:
            errors.append(f"{policy['id']}: version must be an integer, not a boolean")
        if policy.get('topic') not in TOPICS:
            errors.append(f"{policy['id']}: unknown routing topic; JSON alone cannot add one")
    for policy in active:
        rule=policy.get('rule')
        if not rule:
            warnings.append(f"{policy['id']}: prose-only policy; no executable rule test was run")
            continue
        for field in rule.get('required',[]):
            if field not in {'volume_ml','standalone'}:
                errors.append(f"{policy['id']}: no initial request extractor for fact {field}")
        invalid=False
        for condition in rule.get('conditions',[]):
            if condition['op'] not in {'eq','gt'}:
                errors.append(f"{policy['id']}: unsupported operator {condition['op']}; inspect/extend runtime first")
                invalid=True
            if condition['op']=='gt' and type(condition['value']) not in (int,float):
                errors.append(f"{policy['id']}: gt threshold must be numeric")
                invalid=True
        if invalid:continue
        outcomes=set()
        for i,case in enumerate(policy['tests'],1):
            tested+=1
            if not isinstance(case.get('facts'),dict) or not isinstance(case.get('query'),str):
                errors.append(f"{policy['id']} example {i}: invalid query/facts")
                continue
            expected=case['expected']
            actual=evaluate_policy(policy,case['facts'])['outcome']
            outcomes.add(expected)
            if actual!=expected:
                errors.append(f"{policy['id']} example {i}: supplied expectation {expected!r} disagrees with implementation {actual!r}")
            if policy['id'] not in {p['id'] for p in store.search(case['query'],policy['topic'])}:
                errors.append(f"{policy['id']} example {i}: owning policy not in lexical top five; use a separate semantic-only dataset if intentional")
        if 'prohibited' not in outcomes:
            warnings.append(f"{policy['id']}: no applicable prohibition example")
        if rule.get('required') and 'needs_information' not in outcomes:
            warnings.append(f"{policy['id']}: no missing-fact example")
        for condition in rule.get('conditions',[]):
            field,value=condition['field'],condition['value']
            if condition['op']=='gt':
                if not any(t['facts'].get(field)==value and t['expected']=='not_prohibited_by_rule' for t in policy['tests']):
                    warnings.append(f"{policy['id']}: no equality-boundary example for {field}")
                if not any(type(t['facts'].get(field)) in (int,float) and t['facts'][field]>value and t['expected']=='prohibited' for t in policy['tests']):
                    warnings.append(f"{policy['id']}: no above-boundary prohibition example for {field}")
    live_count=0
    if cases:
        from evals.run import validate_cases
        additions=[json.loads(line) for line in cases.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        existing_path=repo/'evals/cases.jsonl'
        existing=[] if cases.resolve()==existing_path.resolve() or not existing_path.exists() else [json.loads(line) for line in existing_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        validate_cases(existing+additions)
        live_count=len(additions)
    return {'passed':not errors,'mode':'offline_contract_and_implementation_agreement',
            'baseline_policies':len(base),'pack_policies':len(active),'combined_policies':len(combined),
            'rule_examples_checked':tested,'live_case_contracts_checked':live_count,
            'errors':errors,'warnings':warnings,
            'claim_boundary':'Agreement with implementation is not independent proof of gold-label correctness; no live semantic/model quality measured.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--pack',type=Path,required=True)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--cases',type=Path)
    args=parser.parse_args(argv)
    repo=args.repo.resolve()
    def resolve(value):return value if value is None or value.is_absolute() else repo/value
    try:
        result=audit(repo,resolve(args.pack),resolve(args.baseline),resolve(args.cases))
    except Exception as error:
        print(json.dumps({'passed':False,'errors':[f'{type(error).__name__}: {error}']}))
        return 2
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':sys.exit(main())
