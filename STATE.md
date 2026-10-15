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

## Baseline (2026-10-13): planner + coder + ruff/pytest, reviewer və RAG söndürülü
5/5 keçdi, orta 98.8s: flatten_list 80.3s/1 cəhd, lru_simple 103.4s/3, roman 86.6s/1, text_slug 152.1s/1, word_count 71.4s/1
Dəyişikliklər: analyzer regex və algorithm fallback (eaf0786), maki-test verify ok:True, ~/maki git repo, Windows ehtiyatı C:\maki-backup

## Plan təcrübəsi (2026-10-13)
qwen3 planner: 4561 token, 87s, 411 sətir plan (think=False işləmir, model düşüncəni cavab kimi yazır)
ref 10/10 107s | skip 15/15 21s | coder-planner: sınaqda. Keçmə eynidir, vaxt 5x, token 9x az
Qərar: analyzer simple -> plansız (MAKI_PLAN=auto, defolt). Məhdudiyyət: eval tapşırıqları sadədir, tavan effekti

## Plan təcrübəsi, yekun (sadə tapşırıqlar)
ref 10/10 107s | skip 15/15 21s | coder 15/15 38s | auto 5/5 27s. Keçmə və cəhd sayı eyni, plan yalnız vaxt və token yeyir
lru_simple plan-coder, auto və baseline-da 3 cəhd tələb edib (limitin kənarı)
Eval doymuşdur. Orta çətinlik: eval/tasks/m_* (5 tapşırıq, 2 fayllı), etiketlər m-skip, m-coder, m-qwen3

## Plan təcrübəsi, yekun (sadə tapşırıqlar)
ref 10/10 107s | skip 15/15 21s | coder 15/15 38s | auto 5/5 27s. Keçmə və cəhd sayı eyni, plan yalnız vaxt və token yeyir
lru_simple plan-coder, auto və baseline-da 3 cəhd tələb edib (limitin kənarı)
Eval doymuşdur. Orta çətinlik: eval/tasks/m_* (5 tapşırıq, 2 fayllı), etiketlər m-skip, m-coder, m-qwen3
