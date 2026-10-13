# MAKI STATE (2026-10-13, WSL bərpasından sonra)
## Mühit
WSL2 Ubuntu 26.04, RTX 4050 6GB, RAM 7.6GB, Ollama 0.40.3
~/.ai-env (Open WebUI, py3.12), ~/.maki-env (orkestrator, py3.14), aider: ~/.local/bin
Modellər: qwen-coder-8k (coder, ctx 8192, num_gpu 99, 39 tok/s), qwen3:4b (planner, think=False), nomic-embed-text (RAG)
## İşləyir
- ai-env agent|accept|reject|rag|doctor|clean|gui. crew.py: plan, code, check (ruff, pytest, stub), commit. Reviewer defolt söndürülüb (MAKI_REVIEW=1)
- eval: ~/maki/eval/run_eval.py, 5 tapşırıq, baseline 3/5 qeydə alınıb (flatten_list 80s/1 cəhd, lru_simple 103s/3, roman 87s/1)
- analyzer.py (qaydalar) 4 nümunədə gözlənildiyi kimi işləyir, crew.py-yə qoşulmayıb, capabilities.json yoxdur
- maki-aider (whole format), lokal RAG (~/.maki-rag), maki-test: 36 test keçir
## Açıq işlər (prioritet)
1. ~/maki git repo deyil, 24 .bak fayl. Windows-a ehtiyat nüsxə yoxdur (WSL çökəndə hər şey vhdx içində riskdə idi)
2. baseline: text_slug, word_count yoxdur, nohup ilə işlət
3. verify.py və crew.py.1012-1622 başqa sessiyadan, məzmun bilinmir
4. analyzer: LRUCache domain=general (regex), crew.py-yə qoş, nəticəni record() et
5. maki-test köhnə maki/* branch-lar
6. Open WebUI pipe yazılıb, sınanmayıb
7. token sayğacı, eval-da tries/domain/level, keçən işin qovluğu silinir
## İş qaydası
- crew.py-ni yamaqla yox, bütöv fayl kimi yaz
- iş gedərkən terminala yapışdırma, uzun işləri nohup ilə işlət
- bir dəyişiklik, sonra eyni eval, sonra müqayisə
