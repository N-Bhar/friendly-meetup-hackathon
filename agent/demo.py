"""Interactive local demo. Verification is simulated, not real authentication."""
import argparse
import json
from agent.agent import run_agent
from agent.llm import client_for
from agent.verification import Session
from agent.policies import configured_store


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='Check configured model connectivity')
    parser.add_argument('--semantic',action='store_true',help='Require and prepare real embedding retrieval; never silently use lexical search')
    args=parser.parse_args()
    store=None
    if args.semantic:
        try:
            print('Preparing semantic policy index...')
            store=configured_store(require_semantic=True)
            store.search('Can I send banknotes?',topic='prohibited_items')
            print('EMBEDDINGS: ready ('+store.embedding_model+')')
        except Exception as error:
            print('EMBEDDINGS: unavailable. Set EMBEDDING_MODEL, check its endpoint, and run python -m agent.search_demo --check.')
            raise SystemExit(2) from error
    if args.check:
        failed=False
        for role in ['CLASSIFIER','AGENT','JUDGE']:
            try:
                client,model=client_for(role)
                models={m.id for m in client.models.list().data}
                if model not in models: raise ValueError('Configured model not present')
                print(role+': ready ('+model+')')
            except Exception:
                failed=True
                print(role+': unavailable; check .env, endpoint and downloaded model')
        raise SystemExit(2 if failed else 0)
    print('LOCAL DEMO ONLY: codes are shown to the tester. No messages sent or real identity verified.')
    session=Session()
    while True:
        question=input('Customer (or /quit): ').strip()
        if question=='/quit': break
        result=run_agent(question,session=session,store=store)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        if result['outcome']=='needs_verification':
            import re
            order_id=re.search(r'PP-\d+',question,re.I).group().upper()
            if session.state in {'verification_pending','verification_failed'} and session.order_id==order_id:
                print('Challenge already pending or attempts exhausted. Restart demo for a new challenge.')
                continue
            code=session.start(order_id)
            print('[TESTER ONLY, SIMULATED CHANNEL] Demo code:',code)
            for _ in range(3):
                if session.verify(input('Secure demo code entry (not sent to model): ')):
                    print(json.dumps(run_agent(session.pending_question,session=session,store=store),indent=2,ensure_ascii=False))
                    break
                print(session.state)
                if session.state!='verification_pending': break


if __name__=='__main__': main()
