# LangChain RAG Test Results

## Scope

This test evaluates the final LangChain-based RAG workflow. The workflow retrieves relevant IT support documents from PostgreSQL/pgvector using LangChain PGVector Store and generates answers with Basic LLM Chain and Ollama Chat Model.

| No | Question | Expected Source | Actual Source | Result | Notes |
|---|---|---|---|---|---|
| 1 | VPN bağlantısı kuramıyorum, ne yapmalıyım? | VPN bağlantısı kurulamıyor | VPN bağlantısı kurulamıyor | Pass | Correct source and clear answer |
| 2 | VPN sürekli kopuyor, ne yapmalıyım? | VPN sürekli kopuyor | VPN sürekli kopuyor | Pass | Correct source and clear answer |
| 3 | Şifremi unuttum, nasıl sıfırlayabilirim? | Şifre unutuldu | Şifre unutuldu | Pass | Correct source and clean Turkish |
| 4 | Yazıcıdan çıktı alamıyorum, ne yapmalıyım? | Yazıcıdan çıktı alınamıyor | Yazıcıdan çıktı alınamıyor | Pass | Correct source and clear answer |
| 5 | Merhaba | Static response | Static response | Pass | No vector search required |
| 6 | Bana yemek tarifi ver | Out of scope response | Out of scope response | Pass | Rejected non-IT topic |