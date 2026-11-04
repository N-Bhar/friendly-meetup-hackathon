from io import StringIO
from copy import deepcopy
from types import SimpleNamespace as NS
import json
import pytest
from rich.console import Console
from agent.policies import PolicyStore, build_index, configured_store, checked_vector
from agent.search_demo import SearchDemo, showcase, main


def test_lexical_demo_does_not_call_embedding_factory():
    def forbidden(records):raise AssertionError('No model call allowed')
    demo=SearchDemo('lexical',forbidden)
    result=demo.search('Can I ship cologne?','prohibited_items')
    assert result['mode']=='lexical'
    assert result['results'][0]['policy_id']=='prohibited-perfume'
    assert all('tests' not in h for h in result['results'])
    rank=next(i for i,h in enumerate(demo.last_hits,1) if h['policy']['id']=='prohibited-perfume')
    assert demo.evaluate_selected(rank,{})['outcome']=='needs_information'
    assert demo.evaluate_selected(rank,{'volume_ml':101})['outcome']=='prohibited'


def test_expanding_catalogue_is_in_memory_only():
    from agent.policies import CATALOGUE
    before=CATALOGUE.read_bytes()
    demo=SearchDemo('lexical')
    n=len(demo.store.records)
    demo.set_expanded(True)
    assert len(demo.store.records)==n+3
    assert demo.search('31 ml illustration ink','prohibited_items')['results'][0]['policy_id']=='demo-art-ink'
    demo.set_expanded(False)
    assert len(demo.store.records)==n
    assert CATALOGUE.read_bytes()==before


def test_semantic_demo_requires_a_real_embedder():
    with pytest.raises(ValueError,match='actual embedding'):
        SearchDemo('semantic',lambda records:PolicyStore(records))


def test_rank_trace_and_rule_selection_with_fake_vectors(tmp_path):
    # This tests plumbing, not actual semantic model quality.
    def factory(records):
        def embed(text):
            return [1.,0.] if 'cash' in text.lower() or text=='wallet paper' else [0.,1.]
        entries=build_index(records,tmp_path/'fake.json',embed,'test-only')
        return PolicyStore(records,embed,entries)
    demo=SearchDemo('semantic',factory)
    result=demo.search('wallet paper','prohibited_items')
    assert not result['lexical']
    assert result['results'][0]['policy_id']=='prohibited-cash'
    assert result['results'][0]['semantic']==1
    # Retrieval does not automatically execute a prohibition.
    assert 'outcome' not in result
    assert demo.evaluate_selected(1,{})['applicability']=='explicitly_confirmed_by_demo_operator'


def test_failed_snapshot_change_keeps_previous_store():
    calls=[]
    def factory(records):
        if calls:raise ValueError('Embedding endpoint unavailable')
        calls.append(True)
        return PolicyStore(records,lambda text:[1.],{})
    demo=SearchDemo('semantic',factory)
    before=demo.store
    with pytest.raises(ValueError):demo.set_expanded(True)
    assert demo.store is before and demo.expanded is False


@pytest.mark.parametrize('vector',[[],[0,0],[float('nan')],[float('inf')],['1'],[True]])
def test_bad_embedding_vectors_fail_closed(vector):
    with pytest.raises(ValueError):checked_vector(vector)


def test_explicit_semantic_configuration_fails_without_model(monkeypatch):
    monkeypatch.delenv('EMBEDDING_MODEL',raising=False)
    with pytest.raises(ValueError,match='EMBEDDING_MODEL'):
        configured_store(require_semantic=True)


def test_configured_store_embeds_documents_and_query_without_chat(monkeypatch,tmp_path):
    import agent.llm as llm
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return NS(data=[NS(embedding=[1.,.5])])
    client=NS(base_url='http://fake-embedding-endpoint/v1',embeddings=NS(create=create))
    monkeypatch.setenv('EMBEDDING_MODEL','fake-test-model')
    monkeypatch.setattr(llm,'client_for',lambda role:(client,'fake-test-model'))
    store=configured_store(tmp_path/'semantic.json',require_semantic=True)
    documents=len(calls)
    assert documents==len(store.records)
    assert store.search('cash')
    assert len(calls)==documents+1
    assert store.embedding_model=='fake-test-model'


def test_showcase_reports_unknown_cases_as_unassessed(tmp_path):
    path=tmp_path/'report.jsonl'
    demo=SearchDemo('lexical')
    showcase(demo,Console(file=StringIO()),path)
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    assert len(rows)==24
    unknown=[r for r in rows if not r['expected_policy_ids']]
    assert unknown and all(r['retrieval_passed'] is None for r in unknown)
    assert {r['snapshot'] for r in rows}=={'original','expanded'}
    with pytest.raises(FileExistsError):showcase(demo,Console(file=StringIO()),path)


def test_selection_and_query_validation():
    demo=SearchDemo('lexical')
    with pytest.raises(ValueError):demo.evaluate_selected(1,{})
    with pytest.raises(ValueError):demo.search('')
    with pytest.raises(ValueError):demo.store.search('cash',limit=0)


def test_cli_lexical_check_has_no_live_models():
    assert main(['--mode','lexical','--check'])==0

def test_full_agent_demo_reuses_prepared_semantic_store(monkeypatch):
    import agent.demo as module
    import sys
    store=NS(embedding_model='fake-semantic',search=lambda *a,**k:[])
    monkeypatch.setattr(module,'configured_store',lambda **kw:store)
    monkeypatch.setattr(sys,'argv',['demo','--semantic'])
    answers=iter(['Can I send perfume?','/quit'])
    monkeypatch.setattr('builtins.input',lambda prompt:next(answers))
    seen=[]
    def run(*args,**kwargs):
        seen.append(kwargs['store'])
        return {'outcome':'answered','answer':'Please provide the volume.'}
    monkeypatch.setattr(module,'run_agent',run)
    module.main()
    assert seen==[store]


def test_cli_semantic_failure_does_not_fall_back(monkeypatch,capsys):
    import agent.search_demo as module
    class Broken:
        def __init__(self,*a,**k):raise ValueError('Missing embedding model')
    monkeypatch.setattr(module,'SearchDemo',Broken)
    assert module.main(['--check'])==2
    assert 'No automatic lexical fallback' in capsys.readouterr().out

def test_snapshot_switch_invalidates_previous_selection():
    demo=SearchDemo('lexical')
    demo.search('cash','prohibited_items')
    demo.set_expanded(True)
    with pytest.raises(ValueError):demo.evaluate_selected(1,{})
