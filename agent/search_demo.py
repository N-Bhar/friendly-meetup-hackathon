"""Policy retrieval demo. No chat model required; embeddings are explicit and real."""
import argparse
import json
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from agent.policies import PolicyStore, configured_store, evaluate_policy, explicit_facts, load_policies

ROOT = Path(__file__).parent.parent
ADDITIONS = ROOT / 'evals' / 'fixtures' / 'policy_additions.json'
QUERIES = ROOT / 'evals' / 'fixtures' / 'retrieval_demo.json'


class SearchDemo:
    def __init__(self, mode='semantic', store_factory=None):
        if mode not in {'semantic','lexical'}:
            raise ValueError('Unknown retrieval mode')
        self.mode = mode
        self.base = load_policies()
        self.additions = load_policies(ADDITIONS)
        self.store_factory = store_factory or (lambda records: configured_store(records=records,require_semantic=True))
        self.set_expanded(False)

    def set_expanded(self, expanded):
        records = self.base + (self.additions if expanded else [])
        if len({p['id'] for p in records}) != len(records):
            raise ValueError('Demo additions conflict with active policy IDs')
        # Build first, then swap state: a failed embedding call leaves the old snapshot intact.
        start = time.perf_counter()
        store = self.store_factory(records) if self.mode == 'semantic' else PolicyStore(records)
        if self.mode == 'semantic' and store.embed is None:
            raise ValueError('Semantic mode requires actual embedding vectors')
        self.store = store
        self.lexical = PolicyStore(records)
        self.expanded = expanded
        self.last_hits = []
        self.last_query = ''
        self.preparation_ms = round((time.perf_counter()-start)*1000,2)

    def search(self, query, topic=None):
        start=time.perf_counter()
        lexical=self.lexical.search_with_scores(query,topic)
        hits=self.store.search_with_scores(query,topic)
        self.last_hits=hits
        self.last_query=query
        def project(hit):
            return {k:v for k,v in hit.items() if k!='policy'} | {
                'policy_id':hit['policy']['id'],'version':hit['policy']['version'],
                'text':hit['policy']['text']}
        return {'query':query,'mode':self.mode,'embedding_model':getattr(self.store,'embedding_model',None),
                'snapshot':'expanded' if self.expanded else 'original','policy_count':len(self.store.records),
                'latency_ms':round((time.perf_counter()-start)*1000,2),
                'lexical':[project(h) for h in lexical], 'results':[project(h) for h in hits]}

    def evaluate_selected(self, rank, facts):
        if type(rank) is not int or not 1 <= rank <= len(getattr(self,'last_hits',[])):
            raise ValueError('Select a result from the most recent search')
        policy=self.last_hits[rank-1]['policy']
        if not isinstance(facts,dict):
            raise ValueError('Facts must be an object')
        return evaluate_policy(policy,facts) | {'applicability':'explicitly_confirmed_by_demo_operator'}


def render(console, report):
    console.print(Text(f"{report['snapshot']} / {report['policy_count']} policies / {report['mode']} / {report['latency_ms']} ms"))
    for title,key in [('Keyword + aliases','lexical'),('Selected retrieval mode','results')]:
        table=Table(title=title)
        for label in ['#','Policy','Total','Keyword','Alias','Semantic']:
            table.add_column(label)
        for i,hit in enumerate(report[key],1):
            table.add_row(str(i),hit['policy_id'],f"{hit['score']:.3f}",f"{hit['lexical']:.3f}",str(hit['alias']),f"{hit['semantic']:.3f}")
        console.print(table)
    console.print('Scores explain ranking, not confidence or permission. No prohibition follows from similarity alone.')


def showcase(demo, console, report_path=None):
    cases=json.loads(QUERIES.read_text(encoding='utf-8'))
    rows=[]
    for expanded in [False,True]:
        if demo.expanded != expanded:
            demo.set_expanded(expanded)
        for case in cases:
            report=demo.search(case['query'],case.get('topic'))
            expected=case['expected_expanded' if expanded else 'expected_original']
            actual={h['policy_id'] for h in report['results']}
            # Absence-of-rule cases cannot be judged from top-k retrieval alone.
            passed=set(expected)<=actual if expected else None
            row={**report,'case_id':case['id'],'expected_policy_ids':expected,'retrieval_passed':passed,
                 'assessment':'positive_recall_only' if expected else 'manual_review_no_automatic_allowance',
                 'index_preparation_ms':demo.preparation_ms}
            rows.append(row)
            console.print(Text(case['query']))
            render(console,report)
    scored=[r for r in rows if r['retrieval_passed'] is not None]
    console.print(f"Positive policy retrieval: {sum(r['retrieval_passed'] for r in scored)}/{len(scored)}. Unknown/non-match cases require human review.")
    if report_path:
        report_path=Path(report_path)
        report_path.parent.mkdir(parents=True,exist_ok=True)
        with report_path.open('x',encoding='utf-8') as file:
            file.write('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n')
        console.print(Text(f'Saved {report_path}'))
    return all(r['retrieval_passed'] for r in scored)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['semantic','lexical'],default='semantic')
    parser.add_argument('--check',action='store_true',help='Prepare index and test one embedding query; no chat models needed')
    parser.add_argument('--showcase',action='store_true',help='Run the fixed before/after policy-growth queries')
    parser.add_argument('--report',type=Path,help='New JSONL report path for --showcase; existing files are not overwritten')
    args=parser.parse_args(argv)
    if args.report and not args.showcase:
        parser.error('--report requires --showcase')
    if args.report and args.report.exists():
        parser.error('Report already exists; choose a new filename')
    console=Console()
    try:
        console.print('Preparing policy index. Semantic mode may call the configured embedding endpoint.')
        demo=SearchDemo(args.mode)
        console.print(Text(f'Ready: {args.mode}, {len(demo.store.records)} policies, index preparation {demo.preparation_ms} ms'))
        if args.check:
            render(console,demo.search('Can I send banknotes?','prohibited_items'))
            return 0
        if args.showcase:
            return 0 if showcase(demo,console,args.report) else 1
        console.print('Search demo only: no answering model or identity verification. Commands: /expand, /reset, /quit.')
        while True:
            query=console.input('Question: ').strip()
            if query=='/quit':return 0
            if query in {'/expand','/reset'}:
                demo.set_expanded(query=='/expand')
                console.print(f'Now {len(demo.store.records)} policies. Active catalogue file is unchanged.')
                continue
            if not query:continue
            report=demo.search(query)
            render(console,report)
            choice=console.input('Inspect a rank (1-5), or Enter for next question: ').strip()
            if not choice:continue
            if not choice.isdigit() or not 1<=int(choice)<=len(demo.last_hits):
                console.print('Choose an available result.');continue
            policy=demo.last_hits[int(choice)-1]['policy']
            console.print(Text(policy['text']))
            if console.input('Does this rule apply to the actual item? Type yes to evaluate: ').strip().lower()!='yes':continue
            facts=explicit_facts(query)
            for field in policy.get('rule',{}).get('required',[]):
                if field not in facts:
                    raw=console.input(f'Provide {field} as JSON (number/true/false), or Enter to leave unknown: ').strip()
                    if raw:
                        try:facts[field]=json.loads(raw)
                        except json.JSONDecodeError:console.print('Invalid JSON; fact stays unknown.')
            console.print_json(data=demo.evaluate_selected(int(choice),facts))
    except (EOFError,KeyboardInterrupt):
        return 0
    except Exception as error:
        console.print(Text('Demo could not complete: '+type(error).__name__+'. Check embedding model, endpoint and .env. No automatic lexical fallback was used.'))
        if isinstance(error,(ValueError,FileExistsError)):
            console.print(Text(str(error)))
        return 2


if __name__=='__main__':
    sys.exit(main())
