# RAG Answer Quality Test Results

## Scope

This test evaluates whether the RAG chatbot retrieves the correct mock IT document and generates clear Turkish answers based on the retrieved source.

| No | Question | Expected Source | Actual Source | Result | Notes |
|---|---|---|---|---|---|
| 1 | VPN bağlantısı kuramıyorum, ne yapmalıyım? | vpn-remote-access | vpn-remote-access | Pass | Correct source and clear answer |
| 2 | VPN sürekli kopuyor, ne yapmalıyım? | vpn-remote-access | vpn-remote-access | Pass | Correct source and clear answer |
| 3 | Şifremi unuttum, nasıl sıfırlayabilirim? | password-and-account | password-and-account | Pass | Correct source and clean Turkish |
| 4 | Hesabım kilitlendi, ne yapmalıyım? | password-and-account | password-and-account | Pass | Correct source and clean Turkish |
| 5 | Yazıcıdan çıktı alamıyorum, ne yapmalıyım? | printer-support | printer-support | Pass | Correct source and clear answer |