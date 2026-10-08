```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	User(User)
	Guardrail(Guardrail)
	Supervisor(Supervisor)
	SQL\20Agent\a\28Northwind\20DB\29(SQL Agent
(Northwind DB))
	RAG\20Agent\a\28PubMed\29(RAG Agent
(PubMed))
	Streamlit\20UI(Streamlit UI)
	__end__([<p>__end__</p>]):::last
	Guardrail --> Supervisor;
	RAG\20Agent\a\28PubMed\29 --> Streamlit\20UI;
	SQL\20Agent\a\28Northwind\20DB\29 --> Streamlit\20UI;
	Supervisor --> RAG\20Agent\a\28PubMed\29;
	Supervisor --> SQL\20Agent\a\28Northwind\20DB\29;
	User --> Guardrail;
	__start__ --> User;
	Streamlit\20UI --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```